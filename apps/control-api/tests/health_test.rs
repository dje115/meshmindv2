//! Health endpoint tests.

use axum::{body::Body, http::{Request, StatusCode}};
use meshmind_control_api::api::handlers::{health_response, health_handler};
use meshmind_control_api::api::handlers::AppState;
use meshmind_control_api::auth::AuthConfig;
use std::sync::Arc;
use tower::ServiceExt;

#[test]
fn health_response_has_status_and_version() {
    let r = health_response();
    assert_eq!(r.status, "ok");
    assert!(!r.version.is_empty());
}

/// Integration test: requires Postgres. Run with: cargo test health_handler_returns_ok -- --ignored
#[tokio::test]
#[ignore = "requires Postgres; run with: cargo test -- --ignored"]
async fn health_handler_returns_ok() {
    let pool = sqlx::PgPool::connect(
        &std::env::var("DATABASE_URL").unwrap_or_else(|_| "postgres://meshmind:meshmind@localhost:5432/meshmind".into()),
    )
    .await
    .expect("Postgres required");
    let state = Arc::new(AppState {
        pool,
        auth_config: AuthConfig::from_secret("test"),
    });
    let app = axum::Router::new()
        .route("/health", axum::routing::get(health_handler))
        .with_state(state);
    let req = Request::builder().uri("/health").body(Body::empty()).unwrap();
    let res = app.oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::OK);
}
