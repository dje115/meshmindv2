//! Worker protocol service: register, heartbeat, claim, progress, complete, fail.

use crate::entities::*;
use crate::error::ApiError;
use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

/// Default heartbeat threshold (seconds) before agent is considered stale.
const HEARTBEAT_STALE_SECS: i64 = 90;
/// Default heartbeat threshold (seconds) before agent is considered dead.
const HEARTBEAT_DEAD_SECS: i64 = 300;

/// Registration input.
pub struct RegisterInput {
    pub name: String,
    pub capabilities: Vec<WorkerCapability>,
}

/// Registration result with agent and token.
pub struct RegisterResult {
    pub agent: Agent,
    pub token: String,
}

/// Claim result with job and source config.
pub struct ClaimResult {
    pub job: Job,
    pub source: Source,
    pub job_run_id: Uuid,
    /// Included when job has source_item_id (e.g. docproc jobs).
    pub source_item: Option<SourceItem>,
}

/// Progress update input.
pub struct ProgressInput {
    pub message: Option<String>,
    pub details: Option<serde_json::Value>,
}

/// Completion input.
pub struct CompleteInput {
    pub artifacts: Option<serde_json::Value>,
}

/// Failure input.
pub struct FailInput {
    pub error: String,
}

/// Register a new agent (worker).
pub async fn register(
    pool: &PgPool,
    input: RegisterInput,
) -> Result<RegisterResult, ApiError> {
    if input.name.trim().is_empty() {
        return Err(ApiError::BadRequest("name is required".into()));
    }
    if input.capabilities.is_empty() {
        return Err(ApiError::BadRequest("at least one capability is required".into()));
    }

    let token = format!("wk_{}", Uuid::new_v4().simple());
    let cap_strings: Vec<String> = input
        .capabilities
        .iter()
        .map(|c| format!("{:?}", c).to_lowercase())
        .collect();

    let agent = sqlx::query_as::<_, Agent>(
        r#"INSERT INTO agents (name, capabilities, agent_token, status)
           VALUES ($1, $2, $3, 'active')
           RETURNING id, name, capabilities, status, last_heartbeat, agent_token, created_at, updated_at"#,
    )
    .bind(&input.name)
    .bind(&cap_strings)
    .bind(&token)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("register: {}", e)))?;

    for cap in &input.capabilities {
        sqlx::query(
            r#"INSERT INTO agent_capabilities (agent_id, capability) VALUES ($1, $2)
               ON CONFLICT (agent_id, capability) DO NOTHING"#,
        )
        .bind(agent.id)
        .bind(cap)
        .execute(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("agent_capabilities insert: {}", e)))?;
    }

    Ok(RegisterResult { agent, token })
}

/// Record heartbeat and return updated agent status.
pub async fn heartbeat(pool: &PgPool, agent_id: Uuid) -> Result<Agent, ApiError> {
    let now = Utc::now();
    let agent = sqlx::query_as::<_, Agent>(
        r#"UPDATE agents SET last_heartbeat = $1, updated_at = $1, status = 'active'
           WHERE id = $2 RETURNING id, name, capabilities, status, last_heartbeat, agent_token, created_at, updated_at"#,
    )
    .bind(now)
    .bind(agent_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("heartbeat: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("agent not found".into()))?;
    Ok(agent)
}

/// Mark agents as stale/dead based on heartbeat.
pub async fn mark_stale_agents(pool: &PgPool) -> Result<(), ApiError> {
    let stale_at = Utc::now() - chrono::Duration::seconds(HEARTBEAT_STALE_SECS);
    let dead_at = Utc::now() - chrono::Duration::seconds(HEARTBEAT_DEAD_SECS);
    sqlx::query(
        r#"UPDATE agents SET status = 'stale' WHERE status = 'active' AND last_heartbeat < $1"#,
    )
    .bind(stale_at)
    .execute(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("mark stale: {}", e)))?;
    sqlx::query(
        r#"UPDATE agents SET status = 'dead' WHERE status IN ('active','stale') AND last_heartbeat < $1"#,
    )
    .bind(dead_at)
    .execute(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("mark dead: {}", e)))?;
    Ok(())
}

/// Claim a job for the agent. Uses capability matching and assignment preferences.
/// Atomic claim: only one worker gets the job.
pub async fn claim(
    pool: &PgPool,
    agent_id: Uuid,
    required_capabilities: &[WorkerCapability],
) -> Result<Option<ClaimResult>, ApiError> {
    let agent = crate::services::agents::get(pool, agent_id).await?;
    if !matches!(agent.status, AgentStatus::Active) {
        return Err(ApiError::BadRequest("agent must be active to claim jobs".into()));
    }

    if required_capabilities.is_empty() {
        return Err(ApiError::BadRequest("at least one capability required".into()));
    }

    // Ensure agent has all required capabilities
    for cap in required_capabilities {
        let has = sqlx::query_scalar::<_, bool>(
            r#"SELECT EXISTS(SELECT 1 FROM agent_capabilities WHERE agent_id = $1 AND capability = $2)"#,
        )
        .bind(agent_id)
        .bind(cap)
        .fetch_one(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("cap check: {}", e)))?;
        if !has {
            return Err(ApiError::BadRequest(format!(
                "agent missing required capability: {:?}",
                cap
            )));
        }
    }

    // Capability strings for SQL ANY
    let cap_strs: Vec<String> = required_capabilities
        .iter()
        .map(|c| format!("{:?}", c).to_lowercase())
        .collect();

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("tx begin: {}", e)))?;

    // Find a queued job: prefer assigned source, else any matching capability.
    // When job_kind is set (ocr, image, docproc), match by job_kind. Else map source kind to capability.
    let job = sqlx::query_as::<_, Job>(
        r#"SELECT j.id, j.source_id, j.source_item_id, j.agent_id, j.job_kind, j.status, j.claimed_at, j.completed_at, j.error,
                  COALESCE(j.retry_count, 0) as retry_count,
                  COALESCE(j.max_retries, 3) as max_retries,
                  j.next_retry_at,
                  j.created_at, j.updated_at
           FROM jobs j
           JOIN sources s ON s.id = j.source_id
           LEFT JOIN agent_assignments aa ON aa.source_id = j.source_id AND aa.agent_id = $1
           WHERE j.status = 'queued'
             AND (j.next_retry_at IS NULL OR j.next_retry_at <= now())
             AND (aa.id IS NOT NULL
                  OR (COALESCE(j.job_kind::text, CASE s.kind
                        WHEN 'filesystem' THEN 'filesystem'
                        ELSE 'docproc'
                      END) = ANY($2::text[])))
             AND EXISTS (
               SELECT 1 FROM agent_capabilities ac
               WHERE ac.agent_id = $1 AND ac.capability::text = ANY($2::text[])
             )
           ORDER BY aa.id IS NOT NULL DESC, j.created_at ASC
           LIMIT 1
           FOR UPDATE SKIP LOCKED"#,
    )
    .bind(agent_id)
    .bind(&cap_strs)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("claim select: {}", e)))?;

    let Some(job) = job else {
        let _ = tx.rollback().await;
        return Ok(None);
    };

    let now = Utc::now();

    // Update job: claimed by this agent
    let job = sqlx::query_as::<_, Job>(
        r#"UPDATE jobs SET agent_id = $1, status = 'claimed', claimed_at = $2, updated_at = $2
           WHERE id = $3
           RETURNING id, source_id, source_item_id, agent_id, job_kind, status, claimed_at, completed_at, error,
                     COALESCE(retry_count, 0) as retry_count,
                     COALESCE(max_retries, 3) as max_retries,
                     next_retry_at, created_at, updated_at"#,
    )
    .bind(agent_id)
    .bind(now)
    .bind(job.id)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("claim update: {}", e)))?;

    // Create job_run
    let job_run = sqlx::query_as::<_, JobRun>(
        r#"INSERT INTO job_runs (job_id, agent_id, status)
           VALUES ($1, $2, 'running')
           RETURNING id, job_id, agent_id, status, started_at, ended_at, error, created_at, updated_at"#,
    )
    .bind(job.id)
    .bind(agent_id)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("job_run insert: {}", e)))?;

    tx.commit()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("claim commit: {}", e)))?;

    let source = crate::services::sources::get(pool, job.source_id).await?;
    let source_item = match job.source_item_id {
        Some(id) => Some(crate::services::source_items::get(pool, id).await?),
        None => None,
    };

    Ok(Some(ClaimResult {
        job,
        source,
        job_run_id: job_run.id,
        source_item,
    }))
}

/// Record progress for a claimed job.
pub async fn progress(
    pool: &PgPool,
    agent_id: Uuid,
    job_id: Uuid,
    job_run_id: Uuid,
    input: ProgressInput,
) -> Result<(), ApiError> {
    let job = crate::services::jobs::get(pool, job_id).await?;
    if job.agent_id != Some(agent_id) {
        return Err(ApiError::Forbidden("job not claimed by this agent".into()));
    }
    if job.status != JobStatus::Claimed {
        return Err(ApiError::Conflict("job is not in claimed state".into()));
    }

    let details = input.details.unwrap_or(serde_json::json!({}));
    let message = input.message.unwrap_or_else(|| "progress".to_string());

    sqlx::query(
        r#"INSERT INTO job_logs (job_id, job_run_id, agent_id, level, message, details)
           VALUES ($1, $2, $3, 'info', $4, $5)"#,
    )
    .bind(job_id)
    .bind(job_run_id)
    .bind(agent_id)
    .bind(&message)
    .bind(&details)
    .execute(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("progress: {}", e)))?;
    Ok(())
}

/// Mark job as completed.
pub async fn complete(
    pool: &PgPool,
    agent_id: Uuid,
    job_id: Uuid,
    job_run_id: Uuid,
    input: CompleteInput,
) -> Result<(), ApiError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("tx: {}", e)))?;

    let job = crate::services::jobs::get(&mut *tx, job_id).await?;
    if job.agent_id != Some(agent_id) {
        let _ = tx.rollback().await;
        return Err(ApiError::Forbidden("job not claimed by this agent".into()));
    }
    if job.status != JobStatus::Claimed {
        let _ = tx.rollback().await;
        return Err(ApiError::Conflict("job is not in claimed state".into()));
    }

    let now = Utc::now();

    sqlx::query(
        r#"UPDATE jobs SET status = 'completed', completed_at = $1, error = NULL, updated_at = $1
           WHERE id = $2"#,
    )
    .bind(now)
    .bind(job_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("complete job: {}", e)))?;

    sqlx::query(
        r#"UPDATE job_runs SET status = 'completed', ended_at = $1, updated_at = $1 WHERE id = $2"#,
    )
    .bind(now)
    .bind(job_run_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("complete run: {}", e)))?;

    if let Some(artifacts) = input.artifacts {
        sqlx::query(
            r#"INSERT INTO job_logs (job_id, job_run_id, agent_id, level, message, details)
               VALUES ($1, $2, $3, 'info', 'completed', $4)"#,
        )
        .bind(job_id)
        .bind(job_run_id)
        .bind(agent_id)
        .bind(&artifacts)
        .execute(&mut *tx)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("complete log: {}", e)))?;
    }

    tx.commit()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("complete commit: {}", e)))?;
    Ok(())
}

/// Mark job as failed. Control plane will handle retry/backoff.
pub async fn fail(
    pool: &PgPool,
    agent_id: Uuid,
    job_id: Uuid,
    job_run_id: Uuid,
    input: FailInput,
) -> Result<(), ApiError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("tx: {}", e)))?;

    let job = crate::services::jobs::get(&mut *tx, job_id).await?;
    if job.agent_id != Some(agent_id) {
        let _ = tx.rollback().await;
        return Err(ApiError::Forbidden("job not claimed by this agent".into()));
    }
    if job.status != JobStatus::Claimed {
        let _ = tx.rollback().await;
        return Err(ApiError::Conflict("job is not in claimed state".into()));
    }

    let now = Utc::now();
    let retry_count = job.retry_count + 1;
    let max_retries = job.max_retries;
    let can_retry = retry_count < max_retries;
    let next_retry = if can_retry {
        // Exponential backoff: 30s, 60s, 120s...
        let delay_secs = 30 * (1 << retry_count);
        Some(now + chrono::Duration::seconds(delay_secs))
    } else {
        None
    };

    let new_status: JobStatus = if can_retry {
        JobStatus::Queued
    } else {
        JobStatus::Failed
    };

    // Reset job for retry: clear agent, status queued, set next_retry_at
    sqlx::query(
        r#"UPDATE jobs SET status = $1, agent_id = NULL, claimed_at = NULL, error = $2,
                  retry_count = $3, next_retry_at = $4, updated_at = $5
           WHERE id = $6"#,
    )
    .bind(new_status)
    .bind(&input.error)
    .bind(retry_count)
    .bind(next_retry)
    .bind(now)
    .bind(job_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("fail job: {}", e)))?;

    sqlx::query(
        r#"UPDATE job_runs SET status = 'failed', ended_at = $1, error = $2, updated_at = $1 WHERE id = $3"#,
    )
    .bind(now)
    .bind(&input.error)
    .bind(job_run_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("fail run: {}", e)))?;

    let details = serde_json::json!({ "retry_count": retry_count });
    sqlx::query(
        r#"INSERT INTO job_logs (job_id, job_run_id, agent_id, level, message, details)
           VALUES ($1, $2, $3, 'error', $4, $5)"#,
    )
    .bind(job_id)
    .bind(job_run_id)
    .bind(agent_id)
    .bind(&input.error)
    .bind(&details)
    .execute(&mut *tx)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("fail log: {}", e)))?;

    tx.commit()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("fail commit: {}", e)))?;
    Ok(())
}

/// Fetch artifacts from the most recent completed job for a source item and job kind.
/// Used by enrich/embed workers to get input from docproc/ocr/image/enrich jobs.
pub async fn get_artifacts_for_source_item(
    pool: &PgPool,
    source_item_id: Uuid,
    job_kind: WorkerCapability,
) -> Result<Option<serde_json::Value>, ApiError> {
    let job = sqlx::query_scalar::<_, Uuid>(
        r#"SELECT j.id FROM jobs j
           WHERE j.source_item_id = $1
             AND j.job_kind = $2
             AND j.status = 'completed'
           ORDER BY j.completed_at DESC
           LIMIT 1"#,
    )
    .bind(source_item_id)
    .bind(job_kind)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("get artifacts job: {}", e)))?;

    let Some(job_id) = job else {
        return Ok(None);
    };

    let row: Option<(serde_json::Value,)> = sqlx::query_as(
        r#"SELECT jl.details FROM job_logs jl
           WHERE jl.job_id = $1 AND jl.message = 'completed'
           ORDER BY jl.created_at DESC
           LIMIT 1"#,
    )
    .bind(job_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("get artifacts: {}", e)))?;

    Ok(row.map(|(d,)| d))
}

/// Assign a source to an agent (source-to-worker assignment).
pub async fn assign_source(
    pool: &PgPool,
    source_id: Uuid,
    agent_id: Uuid,
) -> Result<AgentAssignment, ApiError> {
    let a = sqlx::query_as::<_, AgentAssignment>(
        r#"INSERT INTO agent_assignments (source_id, agent_id)
           VALUES ($1, $2)
           ON CONFLICT (source_id) DO UPDATE SET agent_id = $2, assigned_at = now()
           RETURNING id, source_id, agent_id, assigned_at, created_at"#,
    )
    .bind(source_id)
    .bind(agent_id)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("assign: {}", e)))?;
    Ok(a)
}
