//! MeshMind v2 - Control API
//!
//! Server-first control plane. Orchestrates workers, sources, search, chat.

use anyhow::Result;
use axum::response::IntoResponse;
use meshmind_control_api::api::{self, handlers::AppState};
use meshmind_control_api::auth::AuthConfig;
use meshmind_control_api::config::Config;
use meshmind_control_api::db;
use meshmind_control_api::services::workers;
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

/// Interval (seconds) for the agent status cleanup task.
/// Mark stale: 90s without heartbeat; dead: 300s. Run every 60s.
const AGENT_STATUS_CLEANUP_INTERVAL_SECS: u64 = 60;

/// Background task that periodically marks agents as stale or dead based on
/// last_heartbeat. Thresholds: stale after 90s, dead after 300s.
async fn agent_status_cleanup_task(pool: sqlx::PgPool) {
    let mut interval =
        tokio::time::interval(std::time::Duration::from_secs(AGENT_STATUS_CLEANUP_INTERVAL_SECS));
    interval.tick().await; // First tick fires immediately; skip it
    loop {
        interval.tick().await;
        if let Err(e) = workers::mark_stale_agents(&pool).await {
            tracing::warn!(error = %e, "agent status cleanup failed");
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let config = Config::load()?;
    let pool = db::create_pool(&config).await?;
    db::migrate(&pool).await?;
    db::seed_dev_admin(&pool).await?;

    let auth_config = AuthConfig::from_secret(&config.jwt_secret);
    let state = Arc::new(AppState {
        pool: pool.clone(),
        auth_config: auth_config.clone(),
        query_api_url: config.query_api_url.clone(),
        ollama_url: config.ollama_url.clone(),
        qdrant_url: config.qdrant_url.clone(),
    });

    // Background task: mark agents stale/dead based on last_heartbeat.
    tokio::spawn(agent_status_cleanup_task(pool.clone()));

    let state_for_ready = state.clone();
    let app = api::router(state)
        .route(
            "/health",
            axum::routing::get(|| async { axum::Json(api::health_response()) }),
        )
        .route("/ready", axum::routing::get(move || {
            let s = state_for_ready.clone();
            async move {
                if sqlx::query("SELECT 1").execute(&s.pool).await.is_ok() {
                    axum::Json(serde_json::json!({"status": "ok", "database": "connected"}))
                        .into_response()
                } else {
                    (
                        axum::http::StatusCode::SERVICE_UNAVAILABLE,
                        axum::Json(serde_json::json!({"status": "error", "database": "disconnected"})),
                    )
                        .into_response()
                }
            }
        }));

    tracing::info!(
        bind = %config.http_bind,
        "MeshMind v2 control-api starting"
    );

    let listener = tokio::net::TcpListener::bind(&config.http_bind).await?;
    tracing::info!(bind = %config.http_bind, "listening");
    axum::serve(listener, app).await?;

    Ok(())
}
