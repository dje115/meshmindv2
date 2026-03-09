//! Job service (list, get, create for control plane).

use crate::entities::{Job, WorkerCapability};
use crate::error::ApiError;
use sqlx::PgPool;
use uuid::Uuid;

/// Job kind for downstream dispatch.
pub type JobKind = WorkerCapability;

pub async fn list(
    pool: &PgPool,
    source_id: Option<Uuid>,
    status: Option<&str>,
    limit: i64,
) -> Result<Vec<Job>, ApiError> {
    let limit = limit.clamp(1, 100);
    let jobs = match (source_id, status) {
        (Some(sid), Some(st)) => {
            sqlx::query_as::<_, Job>(
                r#"SELECT * FROM jobs WHERE source_id = $1 AND status::text = $2 ORDER BY created_at DESC LIMIT $3"#,
            )
            .bind(sid)
            .bind(st)
            .bind(limit)
            .fetch_all(pool)
        }
        (Some(sid), None) => {
            sqlx::query_as::<_, Job>(
                r#"SELECT * FROM jobs WHERE source_id = $1 ORDER BY created_at DESC LIMIT $2"#,
            )
            .bind(sid)
            .bind(limit)
            .fetch_all(pool)
        }
        (None, Some(st)) => {
            sqlx::query_as::<_, Job>(
                r#"SELECT * FROM jobs WHERE status::text = $1 ORDER BY created_at DESC LIMIT $2"#,
            )
            .bind(st)
            .bind(limit)
            .fetch_all(pool)
        }
        (None, None) => {
            sqlx::query_as::<_, Job>(r#"SELECT * FROM jobs ORDER BY created_at DESC LIMIT $1"#)
                .bind(limit)
                .fetch_all(pool)
        }
    }
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("jobs list: {}", e)))?;
    Ok(jobs)
}

pub async fn get<'e, E>(exec: E, id: Uuid) -> Result<Job, ApiError>
where
    E: sqlx::Executor<'e, Database = sqlx::Postgres>,
{
    let job = sqlx::query_as::<_, Job>(
        r#"SELECT id, source_id, source_item_id, agent_id, job_kind, status, claimed_at, completed_at, error,
                  COALESCE(retry_count, 0) as retry_count,
                  COALESCE(max_retries, 3) as max_retries,
                  next_retry_at, created_at, updated_at
           FROM jobs WHERE id = $1"#,
    )
    .bind(id)
    .fetch_optional(exec)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("job get: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("job not found".into()))?;
    Ok(job)
}

/// Create a job (control plane owns job creation, e.g. on ingest trigger).
pub async fn create(pool: &PgPool, source_id: Uuid) -> Result<Job, ApiError> {
    let job = sqlx::query_as::<_, Job>(
        r#"INSERT INTO jobs (source_id, status)
           VALUES ($1, 'queued')
           RETURNING id, source_id, source_item_id, agent_id, job_kind, status, claimed_at, completed_at, error,
                     COALESCE(retry_count, 0) as retry_count,
                     COALESCE(max_retries, 3) as max_retries,
                     next_retry_at, created_at, updated_at"#,
    )
    .bind(source_id)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("job create: {}", e)))?;
    Ok(job)
}

/// Create a job for a source item (downstream dispatch: docproc, image, etc.).
pub async fn create_for_item(
    pool: &PgPool,
    source_id: Uuid,
    source_item_id: Uuid,
    job_kind: JobKind,
) -> Result<Job, ApiError> {
    let job = sqlx::query_as::<_, Job>(
        r#"INSERT INTO jobs (source_id, source_item_id, job_kind, status)
           VALUES ($1, $2, $3, 'queued')
           RETURNING id, source_id, source_item_id, agent_id, job_kind, status, claimed_at, completed_at, error,
                     COALESCE(retry_count, 0) as retry_count,
                     COALESCE(max_retries, 3) as max_retries,
                     next_retry_at, created_at, updated_at"#,
    )
    .bind(source_id)
    .bind(source_item_id)
    .bind(job_kind)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("job create_for_item: {}", e)))?;
    Ok(job)
}
