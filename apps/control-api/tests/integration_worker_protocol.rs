//! Worker protocol integration tests. Requires Postgres.
//! Run: cargo test integration_worker -- --ignored

use axum::body::Body;
use axum::http::{Request, StatusCode};
use meshmind_control_api::api::handlers::AppState;
use meshmind_control_api::api::router;
use meshmind_control_api::auth::AuthConfig;
use meshmind_control_api::db;
use meshmind_control_api::entities::SourceKind;
use meshmind_control_api::services::{jobs, sources, workers, workspaces};
use std::sync::Arc;
use tower::ServiceExt;
use uuid::Uuid;

fn db_url() -> String {
    std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://meshmind:meshmind@localhost:5432/meshmind".into())
}

async fn setup_app() -> (axum::Router, sqlx::PgPool) {
    let pool = sqlx::PgPool::connect(&db_url()).await.expect("Postgres required");
    db::migrate(&pool).await.expect("migrate");
    let _ = db::seed_dev_admin(&pool).await;

    let state = Arc::new(AppState {
        pool: pool.clone(),
        auth_config: AuthConfig::from_secret("test-secret"),
        query_api_url: "http://localhost:3001".to_string(),
        ollama_url: "http://localhost:11434".to_string(),
        qdrant_url: "http://localhost:6333".to_string(),
    });
    let app = router(state);
    (app, pool)
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn worker_register_returns_agent_id_and_token() {
    let (app, _pool) = setup_app().await;

    let body = serde_json::json!({
        "name": "test-worker-1",
        "capabilities": ["filesystem", "docproc"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();

    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    let body = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert!(json.get("agent_id").is_some());
    assert!(json.get("token").unwrap().as_str().unwrap().starts_with("wk_"));
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn worker_heartbeat_updates_last_heartbeat() {
    let (app, pool) = setup_app().await;

    // Register
    let body = serde_json::json!({
        "name": "heartbeat-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = json.get("agent_id").unwrap().as_str().unwrap();

    // Heartbeat
    let body = serde_json::json!({ "agent_id": agent_id });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/heartbeat")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    let body = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert_eq!(json.get("status").unwrap(), "active");
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn worker_claim_returns_job_when_available() {
    let (app, pool) = setup_app().await;

    // Create workspace, source, job
    let ws = workspaces::create(
        &pool,
        meshmind_control_api::services::workspaces::CreateWorkspace {
            name: "test".into(),
            slug: "test".into(),
            description: None,
        },
    )
    .await
    .unwrap();
    let source = sources::create(
        &pool,
        meshmind_control_api::services::sources::CreateSource {
            workspace_id: ws.id,
            name: "fs1".into(),
            kind: SourceKind::Filesystem,
            config: None,
        },
    )
    .await
    .unwrap();
    jobs::create(&pool, source.id).await.unwrap();

    // Register agent
    let body = serde_json::json!({
        "name": "claim-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = json.get("agent_id").unwrap().as_str().unwrap();

    // Claim
    let body = serde_json::json!({
        "agent_id": agent_id,
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/jobs/claim")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    let body = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert!(json.get("job_id").is_some());
    assert!(json.get("job_run_id").is_some());
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn worker_claim_no_job_returns_204() {
    let (app, _pool) = setup_app().await;

    let body = serde_json::json!({
        "name": "no-job-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = json.get("agent_id").unwrap().as_str().unwrap();

    let body = serde_json::json!({
        "agent_id": agent_id,
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/jobs/claim")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::NO_CONTENT);
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn worker_complete_marks_job_done() {
    let (app, pool) = setup_app().await;

    let ws = workspaces::create(
        &pool,
        meshmind_control_api::services::workspaces::CreateWorkspace {
            name: "test2".into(),
            slug: "test2".into(),
            description: None,
        },
    )
    .await
    .unwrap();
    let source = sources::create(
        &pool,
        meshmind_control_api::services::sources::CreateSource {
            workspace_id: ws.id,
            name: "fs2".into(),
            kind: SourceKind::Filesystem,
            config: None,
        },
    )
    .await
    .unwrap();
    let job = jobs::create(&pool, source.id).await.unwrap();

    let body = serde_json::json!({
        "name": "complete-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = json.get("agent_id").unwrap().as_str().unwrap();

    let body = serde_json::json!({
        "agent_id": agent_id,
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/jobs/claim")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let job_run_id = json.get("job_run_id").unwrap().as_str().unwrap();

    let body = serde_json::json!({
        "agent_id": agent_id,
        "job_run_id": job_run_id,
        "artifacts": []
    });
    let req = Request::builder()
        .method("POST")
        .uri(format!("/api/workers/jobs/{}/complete", job.id))
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    let job_after = jobs::get(&pool, job.id).await.unwrap();
    assert_eq!(
        format!("{:?}", job_after.status).to_lowercase(),
        "completed"
    );
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn lost_heartbeat_mark_stale_agents() {
    let (app, pool) = setup_app().await;

    let body = serde_json::json!({
        "name": "stale-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = Uuid::parse_str(json.get("agent_id").unwrap().as_str().unwrap()).unwrap();

    sqlx::query(
        r#"UPDATE agents SET last_heartbeat = now() - interval '120 seconds' WHERE id = $1"#,
    )
    .bind(agent_id)
    .execute(&pool)
    .await
    .unwrap();

    workers::mark_stale_agents(&pool).await.unwrap();
    let agent = meshmind_control_api::services::agents::get(&pool, agent_id).await.unwrap();
    assert_eq!(
        format!("{:?}", agent.status).to_lowercase(),
        "stale",
        "agent with 120s old heartbeat should be marked stale"
    );
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn agent_status_cleanup_background_task_updates_stale() {
    let (app, pool) = setup_app().await;

    let body = serde_json::json!({
        "name": "bg-stale-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = Uuid::parse_str(json.get("agent_id").unwrap().as_str().unwrap()).unwrap();

    sqlx::query(
        r#"UPDATE agents SET last_heartbeat = now() - interval '120 seconds' WHERE id = $1"#,
    )
    .bind(agent_id)
    .execute(&pool)
    .await
    .unwrap();

    let pool_clone = pool.clone();
    let handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(std::time::Duration::from_millis(50));
        interval.tick().await;
        for _ in 0..3 {
            interval.tick().await;
            let _ = workers::mark_stale_agents(&pool_clone).await;
        }
    });
    let _ = tokio::time::timeout(std::time::Duration::from_secs(2), handle).await;

    let agent = meshmind_control_api::services::agents::get(&pool, agent_id).await.unwrap();
    assert_eq!(
        format!("{:?}", agent.status).to_lowercase(),
        "stale",
        "background task should mark agent stale"
    );
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn duplicate_claim_prevention_only_one_worker_gets_job() {
    let (app, pool) = setup_app().await;

    let ws = workspaces::create(
        &pool,
        meshmind_control_api::services::workspaces::CreateWorkspace {
            name: "dup-test".into(),
            slug: "dup-test".into(),
            description: None,
        },
    )
    .await
    .unwrap();
    let source = sources::create(
        &pool,
        meshmind_control_api::services::sources::CreateSource {
            workspace_id: ws.id,
            name: "dup-src".into(),
            kind: SourceKind::Filesystem,
            config: None,
        },
    )
    .await
    .unwrap();
    jobs::create(&pool, source.id).await.unwrap();

    let body = serde_json::json!({
        "name": "worker-a",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json_a: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_a = json_a.get("agent_id").unwrap().as_str().unwrap();

    let body = serde_json::json!({
        "name": "worker-b",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json_b: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_b = json_b.get("agent_id").unwrap().as_str().unwrap();

    let claim_body = serde_json::json!({
        "agent_id": agent_a,
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/jobs/claim")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&claim_body).unwrap()))
        .unwrap();
    let res_a = app.clone().oneshot(req).await.unwrap();
    assert_eq!(res_a.status(), StatusCode::OK);

    let claim_body = serde_json::json!({
        "agent_id": agent_b,
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/jobs/claim")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&claim_body).unwrap()))
        .unwrap();
    let res_b = app.oneshot(req).await.unwrap();
    assert_eq!(res_b.status(), StatusCode::NO_CONTENT);
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test integration_worker -- --ignored"]
async fn worker_fail_records_error_and_queues_retry() {
    let (app, pool) = setup_app().await;

    let ws = workspaces::create(
        &pool,
        meshmind_control_api::services::workspaces::CreateWorkspace {
            name: "test3".into(),
            slug: "test3".into(),
            description: None,
        },
    )
    .await
    .unwrap();
    let source = sources::create(
        &pool,
        meshmind_control_api::services::sources::CreateSource {
            workspace_id: ws.id,
            name: "fs3".into(),
            kind: SourceKind::Filesystem,
            config: None,
        },
    )
    .await
    .unwrap();
    let job = jobs::create(&pool, source.id).await.unwrap();

    let body = serde_json::json!({
        "name": "fail-worker",
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/register")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let agent_id = json.get("agent_id").unwrap().as_str().unwrap();

    let body = serde_json::json!({
        "agent_id": agent_id,
        "capabilities": ["filesystem"]
    });
    let req = Request::builder()
        .method("POST")
        .uri("/api/workers/jobs/claim")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap())
            .unwrap();
    let job_run_id = json.get("job_run_id").unwrap().as_str().unwrap();

    let body = serde_json::json!({
        "agent_id": agent_id,
        "job_run_id": job_run_id,
        "error": "extraction failed"
    });
    let req = Request::builder()
        .method("POST")
        .uri(format!("/api/workers/jobs/{}/fail", job.id))
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();
    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    let job_after = jobs::get(&pool, job.id).await.unwrap();
    assert_eq!(job_after.retry_count, 1);
    assert_eq!(job_after.status, meshmind_control_api::entities::JobStatus::Queued);
    assert!(job_after.next_retry_at.is_some());
}
