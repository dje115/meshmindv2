//! Workspace service.

use crate::entities::Workspace;
use crate::error::ApiError;
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct CreateWorkspace {
    pub name: String,
    pub slug: String,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateWorkspace {
    pub name: Option<String>,
    pub slug: Option<String>,
    pub description: Option<String>,
}

pub async fn list(pool: &PgPool) -> Result<Vec<Workspace>, ApiError> {
    let workspaces = sqlx::query_as::<_, Workspace>(r#"SELECT * FROM workspaces ORDER BY name"#)
        .fetch_all(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("workspaces list: {}", e)))?;
    Ok(workspaces)
}

pub async fn get(pool: &PgPool, id: Uuid) -> Result<Workspace, ApiError> {
    let ws = sqlx::query_as::<_, Workspace>(r#"SELECT * FROM workspaces WHERE id = $1"#)
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("workspace get: {}", e)))?
        .ok_or_else(|| ApiError::NotFound("workspace not found".into()))?;
    Ok(ws)
}

pub async fn create(pool: &PgPool, input: CreateWorkspace) -> Result<Workspace, ApiError> {
    let id = Uuid::new_v4();
    let ws = sqlx::query_as::<_, Workspace>(
        r#"
        INSERT INTO workspaces (id, name, slug, description)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(&input.name)
    .bind(&input.slug)
    .bind(&input.description)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        if let Some(db_err) = e.as_database_error() {
            if db_err.constraint().is_some() {
                return ApiError::Conflict("workspace slug already exists".into());
            }
        }
        ApiError::Internal(anyhow::anyhow!("workspace create: {}", e))
    })?;
    Ok(ws)
}

pub async fn update(pool: &PgPool, id: Uuid, input: UpdateWorkspace) -> Result<Workspace, ApiError> {
    let ws = sqlx::query_as::<_, Workspace>(
        r#"
        UPDATE workspaces SET
            name = COALESCE($2, name),
            slug = COALESCE($3, slug),
            description = COALESCE($4, description),
            updated_at = now()
        WHERE id = $1
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(&input.name)
    .bind(&input.slug)
    .bind(&input.description)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("workspace update: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("workspace not found".into()))?;
    Ok(ws)
}

/// Workspace IDs the user has access to.
pub async fn ids_for_user(pool: &PgPool, user_id: Uuid) -> Result<Vec<Uuid>, ApiError> {
    let rows = sqlx::query_scalar::<_, Uuid>(
        r#"SELECT workspace_id FROM workspace_users WHERE user_id = $1"#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("workspace_ids: {}", e)))?;
    Ok(rows)
}

pub async fn delete(pool: &PgPool, id: Uuid) -> Result<(), ApiError> {
    let r = sqlx::query(r#"DELETE FROM workspaces WHERE id = $1"#)
        .bind(id)
        .execute(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("workspace delete: {}", e)))?;
    if r.rows_affected() == 0 {
        return Err(ApiError::NotFound("workspace not found".into()));
    }
    Ok(())
}
