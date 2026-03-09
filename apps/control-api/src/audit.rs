//! Audit event creation hooks.

use crate::entities::AuditEvent;
use crate::error::ApiError;
use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

/// Create an audit event.
pub async fn create(
    pool: &PgPool,
    workspace_id: Option<Uuid>,
    user_id: Option<Uuid>,
    action: &str,
    resource_type: &str,
    resource_id: Option<Uuid>,
    request_id: Option<&str>,
    details: serde_json::Value,
) -> Result<AuditEvent, ApiError> {
    let id = Uuid::new_v4();
    let now = Utc::now();
    sqlx::query_as::<_, AuditEvent>(
        r#"
        INSERT INTO audit_events (id, workspace_id, user_id, action, resource_type, resource_id, request_id, details, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(workspace_id)
    .bind(user_id)
    .bind(action)
    .bind(resource_type)
    .bind(resource_id)
    .bind(request_id)
    .bind(details)
    .bind(now)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("audit create: {}", e)))
}
