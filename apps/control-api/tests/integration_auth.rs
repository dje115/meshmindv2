//! Auth integration tests. Requires Postgres.
//! Run: cargo test integration_auth -- --ignored

use axum::{body::Body, http::{Request, StatusCode}};
use meshmind_control_api::api::handlers::AppState;
use meshmind_control_api::api::router;
use meshmind_control_api::auth::AuthConfig;
use meshmind_control_api::db;
use std::sync::Arc;
use tower::ServiceExt;

fn db_url() -> String {
    std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://meshmind:meshmind@localhost:5432/meshmind".into())
}

#[tokio::test]
#[ignore = "requires Postgres; run: cargo test -- --ignored"]
async fn login_returns_token() {
    let pool = sqlx::PgPool::connect(&db_url()).await.expect("Postgres required");
    db::migrate(&pool).await.expect("migrate");
    let _ = db::seed_dev_admin(&pool).await;

    let state = Arc::new(AppState {
        pool,
        auth_config: AuthConfig::from_secret("test-secret"),
        query_api_url: "http://localhost:3001".to_string(),
        ollama_url: "http://localhost:11434".to_string(),
        qdrant_url: "http://localhost:6333".to_string(),
    });
    let app = router(state);

    let body = serde_json::json!({"username": "admin", "password": "admin"});
    let req = Request::builder()
        .method("POST")
        .uri("/api/auth/login")
        .header("content-type", "application/json")
        .body(Body::from(serde_json::to_string(&body).unwrap()))
        .unwrap();

    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    let body = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert!(json.get("token").unwrap().as_str().unwrap().len() > 0);
    assert_eq!(json.get("user").unwrap().get("username").unwrap(), "admin");
}
