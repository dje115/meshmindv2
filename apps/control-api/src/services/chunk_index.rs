//! Chunk index for keyword search (FTS).

use crate::error::ApiError;
use serde::Deserialize;
use utoipa::ToSchema;
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Deserialize, ToSchema)]
pub struct ChunkInput {
    pub chunk_id: String,
    pub chunk_index: i32,
    pub text: String,
    #[serde(default)]
    pub page_index: Option<i32>,
    #[serde(default)]
    pub sheet_index: Option<i32>,
    #[serde(default)]
    pub sheet_name: Option<String>,
    #[serde(default)]
    pub provenance: Option<serde_json::Value>,
}

/// Upsert chunks for a source item. Replaces existing chunks for that source_item.
pub async fn upsert_chunks(
    pool: &PgPool,
    source_item_id: Uuid,
    source_id: Uuid,
    workspace_id: Uuid,
    chunks: Vec<ChunkInput>,
) -> Result<u64, ApiError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("tx: {}", e)))?;

    sqlx::query("DELETE FROM chunk_index WHERE source_item_id = $1")
        .bind(source_item_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("delete: {}", e)))?;

    let mut count = 0u64;
    for c in chunks {
        if c.text.trim().is_empty() {
            continue;
        }
        let prov = c.provenance.unwrap_or(serde_json::json!({}));
        sqlx::query(
            r#"INSERT INTO chunk_index (source_item_id, source_id, workspace_id, chunk_id, chunk_index, text, page_index, sheet_index, sheet_name, provenance)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
               ON CONFLICT (source_item_id, chunk_id) DO UPDATE SET
                 chunk_index = EXCLUDED.chunk_index,
                 text = EXCLUDED.text,
                 page_index = EXCLUDED.page_index,
                 sheet_index = EXCLUDED.sheet_index,
                 sheet_name = EXCLUDED.sheet_name,
                 provenance = EXCLUDED.provenance"#,
        )
        .bind(source_item_id)
        .bind(source_id)
        .bind(workspace_id)
        .bind(&c.chunk_id)
        .bind(c.chunk_index)
        .bind(&c.text)
        .bind(c.page_index)
        .bind(c.sheet_index)
        .bind(c.sheet_name)
        .bind(&prov)
        .execute(&mut *tx)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("insert: {}", e)))?;
        count += 1;
    }

    tx.commit()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("commit: {}", e)))?;
    Ok(count)
}
