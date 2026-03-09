//! Role service.

use crate::entities::Role;
use crate::error::ApiError;
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct CreateRole {
    pub name: String,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateRole {
    pub description: Option<String>,
}

pub async fn list(pool: &PgPool) -> Result<Vec<Role>, ApiError> {
    let roles = sqlx::query_as::<_, Role>(r#"SELECT * FROM roles ORDER BY name"#)
        .fetch_all(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("roles list: {}", e)))?;
    Ok(roles)
}

pub async fn get(pool: &PgPool, id: Uuid) -> Result<Role, ApiError> {
    let role = sqlx::query_as::<_, Role>(r#"SELECT * FROM roles WHERE id = $1"#)
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("role get: {}", e)))?
        .ok_or_else(|| ApiError::NotFound("role not found".into()))?;
    Ok(role)
}

pub async fn create(pool: &PgPool, input: CreateRole) -> Result<Role, ApiError> {
    let id = Uuid::new_v4();
    let role = sqlx::query_as::<_, Role>(
        r#"
        INSERT INTO roles (id, name, description)
        VALUES ($1, $2, $3)
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(&input.name)
    .bind(&input.description)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        if let Some(db_err) = e.as_database_error() {
            if db_err.constraint().is_some() {
                return ApiError::Conflict("role name already exists".into());
            }
        }
        ApiError::Internal(anyhow::anyhow!("role create: {}", e))
    })?;
    Ok(role)
}

pub async fn update(pool: &PgPool, id: Uuid, input: UpdateRole) -> Result<Role, ApiError> {
    let role = sqlx::query_as::<_, Role>(
        r#"
        UPDATE roles SET description = COALESCE($2, description), updated_at = now()
        WHERE id = $1
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(&input.description)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("role update: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("role not found".into()))?;
    Ok(role)
}

pub async fn delete(pool: &PgPool, id: Uuid) -> Result<(), ApiError> {
    let r = sqlx::query(r#"DELETE FROM roles WHERE id = $1"#)
        .bind(id)
        .execute(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("role delete: {}", e)))?;
    if r.rows_affected() == 0 {
        return Err(ApiError::NotFound("role not found".into()));
    }
    Ok(())
}
