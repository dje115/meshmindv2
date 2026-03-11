//! App settings: UI-configurable preferences stored in DB.

use crate::error::ApiError;
use sqlx::PgPool;
use std::collections::HashMap;

/// Get all settings as category -> key -> value.
pub async fn get_all(pool: &PgPool) -> Result<HashMap<String, HashMap<String, serde_json::Value>>, ApiError> {
    let rows = sqlx::query_as::<_, (String, String, String)>(
        r#"SELECT category, key, value_json FROM app_settings ORDER BY category, key"#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("app_settings get_all: {}", e)))?;

    let mut out: HashMap<String, HashMap<String, serde_json::Value>> = HashMap::new();
    for (category, key, value_json) in rows {
        let val: serde_json::Value = serde_json::from_str(&value_json).unwrap_or(serde_json::Value::Null);
        out.entry(category).or_default().insert(key, val);
    }
    Ok(out)
}

/// Get settings for a category.
pub async fn get_category(pool: &PgPool, category: &str) -> Result<HashMap<String, serde_json::Value>, ApiError> {
    let rows = sqlx::query_as::<_, (String, String)>(
        r#"SELECT key, value_json FROM app_settings WHERE category = $1 ORDER BY key"#,
    )
    .bind(category)
    .fetch_all(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("app_settings get_category: {}", e)))?;

    let mut out = HashMap::new();
    for (key, value_json) in rows {
        let val: serde_json::Value = serde_json::from_str(&value_json).unwrap_or(serde_json::Value::Null);
        out.insert(key, val);
    }
    Ok(out)
}

/// Set a single setting.
pub async fn set(
    pool: &PgPool,
    category: &str,
    key: &str,
    value: serde_json::Value,
) -> Result<(), ApiError> {
    let value_json = serde_json::to_string(&value).map_err(|e| ApiError::Internal(anyhow::anyhow!("serialize: {}", e)))?;
    sqlx::query(
        r#"INSERT INTO app_settings (category, key, value_json, updated_at)
           VALUES ($1, $2, $3, now())
           ON CONFLICT (category, key) DO UPDATE SET value_json = $3, updated_at = now()"#,
    )
    .bind(category)
    .bind(key)
    .bind(&value_json)
    .execute(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("app_settings set: {}", e)))?;
    Ok(())
}

/// Set multiple settings for a category.
pub async fn set_category(
    pool: &PgPool,
    category: &str,
    settings: &HashMap<String, serde_json::Value>,
) -> Result<(), ApiError> {
    for (key, value) in settings {
        set(pool, category, key, value.clone()).await?;
    }
    Ok(())
}
