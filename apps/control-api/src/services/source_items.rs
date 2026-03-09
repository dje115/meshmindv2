//! Source items service (create_batch).

use crate::entities::SourceItem;
use crate::error::ApiError;
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct CreateSourceItem {
    pub fingerprint: String,
    pub provenance: Option<serde_json::Value>,
}

/// Upsert source items in batch. Uses ON CONFLICT (source_id, fingerprint) DO UPDATE.
pub async fn create_batch(
    pool: &PgPool,
    source_id: Uuid,
    items: Vec<CreateSourceItem>,
) -> Result<Vec<SourceItem>, ApiError> {
    if items.is_empty() {
        return Ok(vec![]);
    }

    let mut results = Vec::with_capacity(items.len());
    for item in items {
        let provenance = item.provenance.unwrap_or(serde_json::json!({}));
        let row = sqlx::query_as::<_, SourceItem>(
            r#"INSERT INTO source_items (source_id, fingerprint, provenance)
               VALUES ($1, $2, $3)
               ON CONFLICT (source_id, fingerprint) DO UPDATE SET
                 provenance = EXCLUDED.provenance,
                 updated_at = now()
               RETURNING id, source_id, fingerprint, provenance, created_at, updated_at"#,
        )
        .bind(source_id)
        .bind(&item.fingerprint)
        .bind(&provenance)
        .fetch_one(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("source_items create_batch: {}", e)))?;
        results.push(row);
    }
    Ok(results)
}

pub async fn get(pool: &PgPool, id: Uuid) -> Result<SourceItem, ApiError> {
    let item = sqlx::query_as::<_, SourceItem>(
        r#"SELECT id, source_id, fingerprint, provenance, created_at, updated_at FROM source_items WHERE id = $1"#,
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("source_items get: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("source_item not found".into()))?;
    Ok(item)
}
