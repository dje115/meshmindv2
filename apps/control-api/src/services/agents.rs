//! Agent service (read-only list).

use crate::entities::Agent;
use crate::error::ApiError;
use sqlx::PgPool;
use uuid::Uuid;

pub async fn list(pool: &PgPool, status: Option<&str>) -> Result<Vec<Agent>, ApiError> {
    let agents = if let Some(s) = status {
        sqlx::query_as::<_, Agent>(r#"SELECT * FROM agents WHERE status::text = $1 ORDER BY name"#)
            .bind(s)
            .fetch_all(pool)
    } else {
        sqlx::query_as::<_, Agent>(r#"SELECT * FROM agents ORDER BY name"#).fetch_all(pool)
    }
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("agents list: {}", e)))?;
    Ok(agents)
}

pub async fn get(pool: &PgPool, id: Uuid) -> Result<Agent, ApiError> {
    let agent = sqlx::query_as::<_, Agent>(r#"SELECT * FROM agents WHERE id = $1"#)
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("agent get: {}", e)))?
        .ok_or_else(|| ApiError::NotFound("agent not found".into()))?;
    Ok(agent)
}
