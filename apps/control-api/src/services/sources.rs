//! Source service.

use crate::entities::{Source, SourceKind, SourceStatus};
use crate::error::ApiError;
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct CreateSource {
    pub workspace_id: Uuid,
    pub name: String,
    pub kind: SourceKind,
    pub config: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateSource {
    pub name: Option<String>,
    pub kind: Option<SourceKind>,
    pub config: Option<serde_json::Value>,
    pub status: Option<SourceStatus>,
}

pub async fn list(pool: &PgPool, workspace_id: Option<Uuid>) -> Result<Vec<Source>, ApiError> {
    let sources = if let Some(wid) = workspace_id {
        sqlx::query_as::<_, Source>(r#"SELECT * FROM sources WHERE workspace_id = $1 ORDER BY name"#)
            .bind(wid)
            .fetch_all(pool)
    } else {
        sqlx::query_as::<_, Source>(r#"SELECT * FROM sources ORDER BY name"#).fetch_all(pool)
    }
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("sources list: {}", e)))?;
    Ok(sources)
}

pub async fn get(pool: &PgPool, id: Uuid) -> Result<Source, ApiError> {
    let source = sqlx::query_as::<_, Source>(r#"SELECT * FROM sources WHERE id = $1"#)
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("source get: {}", e)))?
        .ok_or_else(|| ApiError::NotFound("source not found".into()))?;
    Ok(source)
}

pub async fn create(pool: &PgPool, input: CreateSource) -> Result<Source, ApiError> {
    let id = Uuid::new_v4();
    let config = input.config.unwrap_or(serde_json::json!({}));
    let source = sqlx::query_as::<_, Source>(
        r#"
        INSERT INTO sources (id, workspace_id, name, kind, config)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(input.workspace_id)
    .bind(&input.name)
    .bind(input.kind)
    .bind(config)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("source create: {}", e)))?;
    Ok(source)
}

pub async fn update(pool: &PgPool, id: Uuid, input: UpdateSource) -> Result<Source, ApiError> {
    let source = sqlx::query_as::<_, Source>(
        r#"
        UPDATE sources SET
            name = COALESCE($2, name),
            kind = COALESCE($3, kind),
            config = COALESCE($4, config),
            status = COALESCE($5, status),
            updated_at = now()
        WHERE id = $1
        RETURNING *
        "#,
    )
    .bind(id)
    .bind(&input.name)
    .bind(input.kind)
    .bind(&input.config)
    .bind(input.status)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("source update: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("source not found".into()))?;
    Ok(source)
}

pub async fn delete(pool: &PgPool, id: Uuid) -> Result<(), ApiError> {
    let r = sqlx::query(r#"DELETE FROM sources WHERE id = $1"#)
        .bind(id)
        .execute(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("source delete: {}", e)))?;
    if r.rows_affected() == 0 {
        return Err(ApiError::NotFound("source not found".into()));
    }
    Ok(())
}
