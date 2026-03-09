//! Audit events service (list).

use crate::entities::AuditEvent;
use crate::error::ApiError;
use sqlx::PgPool;
use uuid::Uuid;

pub async fn list(
    pool: &PgPool,
    workspace_id: Option<Uuid>,
    user_id: Option<Uuid>,
    limit: i64,
) -> Result<Vec<AuditEvent>, ApiError> {
    let limit = limit.clamp(1, 100);
    let events = match (workspace_id, user_id) {
        (Some(wid), Some(uid)) => {
            sqlx::query_as::<_, AuditEvent>(
                r#"SELECT * FROM audit_events WHERE workspace_id = $1 AND user_id = $2 ORDER BY created_at DESC LIMIT $3"#,
            )
            .bind(wid)
            .bind(uid)
            .bind(limit)
            .fetch_all(pool)
        }
        (Some(wid), None) => {
            sqlx::query_as::<_, AuditEvent>(
                r#"SELECT * FROM audit_events WHERE workspace_id = $1 ORDER BY created_at DESC LIMIT $2"#,
            )
            .bind(wid)
            .bind(limit)
            .fetch_all(pool)
        }
        (None, Some(uid)) => {
            sqlx::query_as::<_, AuditEvent>(
                r#"SELECT * FROM audit_events WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2"#,
            )
            .bind(uid)
            .bind(limit)
            .fetch_all(pool)
        }
        (None, None) => {
            sqlx::query_as::<_, AuditEvent>(r#"SELECT * FROM audit_events ORDER BY created_at DESC LIMIT $1"#)
                .bind(limit)
                .fetch_all(pool)
        }
    }
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("audit list: {}", e)))?;
    Ok(events)
}
