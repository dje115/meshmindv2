//! Permission checks for RBAC.

use crate::error::ApiError;
use sqlx::PgPool;
use uuid::Uuid;

/// Whether the user has the given permission (via any of their roles).
pub async fn user_has_permission(
    pool: &PgPool,
    user_id: Uuid,
    permission_name: &str,
) -> Result<bool, ApiError> {
    let has = sqlx::query_scalar::<_, bool>(
        r#"SELECT EXISTS(
            SELECT 1 FROM user_roles ur
            JOIN role_permissions rp ON rp.role_id = ur.role_id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE ur.user_id = $1 AND p.name = $2
        )"#,
    )
    .bind(user_id)
    .bind(permission_name)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("permission check: {}", e)))?;
    Ok(has)
}
