//! Query layer handlers: search, documents, provenance, ask.

use crate::api::handlers::AppState;
use crate::error::ApiError;
use crate::services::{app_settings, permissions, source_items, sources, workspaces, workers};
use axum::{
    extract::{Path, Query, State},
    Json,
};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct SearchQuery {
    pub q: String,
    #[serde(default)]
    pub source_ids: Option<String>,
    #[serde(default = "default_search_limit")]
    pub limit: i64,
}

fn default_search_limit() -> i64 {
    20
}

#[derive(Debug, Serialize)]
pub struct SearchResponse {
    pub chunks: Vec<serde_json::Value>,
    pub facets: serde_json::Value,
    pub total: usize,
}

#[derive(Debug, Deserialize)]
pub struct AskRequest {
    pub question: String,
    #[serde(default)]
    pub workspace_ids: Option<Vec<String>>,
    #[serde(default)]
    pub source_ids: Option<Vec<String>>,
    #[serde(default = "default_max_chunks")]
    pub max_chunks: i32,
}

fn default_max_chunks() -> i32 {
    10
}

/// Ensure user has permission and return workspace IDs.
async fn require_search_access(
    state: &Arc<AppState>,
    user_id: Uuid,
) -> Result<Vec<Uuid>, ApiError> {
    let has = permissions::user_has_permission(&state.pool, user_id, "search:read").await?;
    if !has {
        return Err(ApiError::Forbidden("search:read permission required".into()));
    }
    let wids = workspaces::ids_for_user(&state.pool, user_id).await?;
    if wids.is_empty() {
        return Err(ApiError::Forbidden(
            "no workspaces assigned; search requires workspace access".into(),
        ));
    }
    Ok(wids)
}

/// Ensure user has ask permission and return workspace IDs.
async fn require_ask_access(state: &Arc<AppState>, user_id: Uuid) -> Result<Vec<Uuid>, ApiError> {
    let has = permissions::user_has_permission(&state.pool, user_id, "ask:read").await?;
    if !has {
        return Err(ApiError::Forbidden("ask:read permission required".into()));
    }
    let wids = workspaces::ids_for_user(&state.pool, user_id).await?;
    if wids.is_empty() {
        return Err(ApiError::Forbidden(
            "no workspaces assigned; ask requires workspace access".into(),
        ));
    }
    Ok(wids)
}

/// Ensure user can access the source item (via source's workspace).
async fn can_access_source_item(
    pool: &sqlx::PgPool,
    user_id: Uuid,
    source_item_id: Uuid,
) -> Result<bool, ApiError> {
    let si = source_items::get(pool, source_item_id).await?;
    let src = sources::get(pool, si.source_id).await?;
    let wids = workspaces::ids_for_user(pool, user_id).await?;
    Ok(wids.contains(&src.workspace_id))
}

pub async fn search(
    State(state): State<Arc<AppState>>,
    auth: crate::auth::AuthUser,
    Query(q): Query<SearchQuery>,
) -> Result<Json<SearchResponse>, ApiError> {
    let wids = require_search_access(&state, auth.user_id).await?;
    let wids_str: Vec<String> = wids.iter().map(|u| u.to_string()).collect();
    let client = Client::new();
    let url = format!("{}/search", state.query_api_url.trim_end_matches('/'));
    let mut query_params: Vec<(&str, String)> = vec![
        ("q", q.q.clone()),
        ("limit", q.limit.to_string()),
    ];
    if let Some(ref sids) = q.source_ids {
        query_params.push(("source_ids", sids.clone()));
    }
    let resp = client
        .get(&url)
        .query(&query_params)
        .header("X-Workspace-Ids", wids_str.join(","))
        .send()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("query-api: {}", e)))?;
    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(ApiError::Internal(anyhow::anyhow!(
            "query-api error {}: {}",
            status,
            body
        )));
    }
    let data: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("query-api json: {}", e)))?;
    let chunks = data.get("chunks").cloned().unwrap_or(serde_json::json!([]));
    let facets = data.get("facets").cloned().unwrap_or(serde_json::json!({}));
    let total = chunks.as_array().map(|a| a.len()).unwrap_or(0);
    Ok(Json(SearchResponse {
        chunks: chunks.as_array().cloned().unwrap_or_default(),
        facets,
        total,
    }))
}

pub async fn document_detail(
    State(state): State<Arc<AppState>>,
    auth: crate::auth::AuthUser,
    Path(id): Path<Uuid>,
) -> Result<Json<serde_json::Value>, ApiError> {
    let can = can_access_source_item(&state.pool, auth.user_id, id).await?;
    if !can {
        return Err(ApiError::Forbidden("access denied".into()));
    }
    let si = source_items::get(&state.pool, id).await?;
    let src = sources::get(&state.pool, si.source_id).await?;
    let artifacts = workers::get_artifacts_for_source_item(
        &state.pool,
        id,
        crate::entities::WorkerCapability::Enrich,
    )
    .await?;
    let chunks = artifacts
        .and_then(|a| {
            a.get("chunks")
                .or_else(|| a.get("enriched_chunks"))
                .cloned()
        })
        .unwrap_or(serde_json::json!([]));
    let doc = serde_json::json!({
        "id": si.id,
        "source_id": si.source_id,
        "workspace_id": src.workspace_id,
        "fingerprint": si.fingerprint,
        "provenance": si.provenance,
        "chunks": chunks,
    });
    Ok(Json(doc))
}

pub async fn document_provenance(
    State(state): State<Arc<AppState>>,
    auth: crate::auth::AuthUser,
    Path(id): Path<Uuid>,
) -> Result<Json<serde_json::Value>, ApiError> {
    let can = can_access_source_item(&state.pool, auth.user_id, id).await?;
    if !can {
        return Err(ApiError::Forbidden("access denied".into()));
    }
    let si = source_items::get(&state.pool, id).await?;
    let src = sources::get(&state.pool, si.source_id).await?;
    let prov = si.provenance.as_object().cloned().unwrap_or_default();
    let absolute_path = prov.get("absolute_path").and_then(|v| v.as_str()).map(String::from);
    let filename = prov.get("filename").and_then(|v| v.as_str()).map(String::from);
    let open_target = prov.get("open_target").and_then(|v| v.as_str()).map(String::from);
    let out = serde_json::json!({
        "source_item_id": si.id,
        "source_id": si.source_id,
        "workspace_id": src.workspace_id,
        "provenance": si.provenance,
        "absolute_path": absolute_path,
        "filename": filename,
        "open_target": open_target,
    });
    Ok(Json(out))
}

pub async fn ask(
    State(state): State<Arc<AppState>>,
    auth: crate::auth::AuthUser,
    Json(req): Json<AskRequest>,
) -> Result<Json<serde_json::Value>, ApiError> {
    let wids = require_ask_access(&state, auth.user_id).await?;
    let wids_str: Vec<String> = wids.iter().map(|u| u.to_string()).collect();
    let client = Client::new();
    let url = format!("{}/ask", state.query_api_url.trim_end_matches('/'));

    // Load app settings and pass to query-api (overrides env/hardcoded)
    let models = app_settings::get_category(&state.pool, "models").await.ok();
    let internet = app_settings::get_category(&state.pool, "internet_research").await.ok();
    let mut settings = serde_json::Map::new();
    if let Some(m) = models {
        if let Some(v) = m.get("ollama_url").and_then(|v| v.as_str()) {
            settings.insert("ollama_url".into(), serde_json::Value::String(v.to_string()));
        }
        if let Some(v) = m.get("embed_model").and_then(|v| v.as_str()) {
            settings.insert("embed_model".into(), serde_json::Value::String(v.to_string()));
        }
        if let Some(v) = m.get("ask_model").and_then(|v| v.as_str()) {
            settings.insert("ask_model".into(), serde_json::Value::String(v.to_string()));
        }
    }
    if let Some(i) = internet {
        if let Some(v) = i.get("enabled").and_then(|v| v.as_bool()) {
            settings.insert("web_research_enabled".into(), serde_json::Value::Bool(v));
        }
    }

    let body = serde_json::json!({
        "question": req.question,
        "workspace_ids": req.workspace_ids.unwrap_or(wids_str.clone()),
        "source_ids": req.source_ids,
        "max_chunks": req.max_chunks,
        "settings": if settings.is_empty() { serde_json::Value::Null } else { serde_json::Value::Object(settings) },
    });
    let resp = client
        .post(&url)
        .header("Content-Type", "application/json")
        .header("X-Workspace-Ids", wids_str.join(","))
        .json(&body)
        .timeout(std::time::Duration::from_secs(120))
        .send()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("query-api: {}", e)))?;
    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(ApiError::Internal(anyhow::anyhow!(
            "query-api error {}: {}",
            status,
            body
        )));
    }
    let data: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("query-api json: {}", e)))?;
    Ok(Json(data))
}
