//! Worker protocol handlers: register, heartbeat, claim, progress, complete, fail.

use axum::response::IntoResponse;

use crate::entities::{SourceItem, WorkerCapability};
use crate::error::ApiError;
use crate::services::{chunk_index, jobs, source_items, sources, workers};
use axum::{extract::Path, extract::Query, extract::State, Json};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use utoipa::ToSchema;
use uuid::Uuid;

use super::handlers::AppState;

// --- Request/Response types ---

#[derive(Debug, Deserialize, ToSchema)]
pub struct RegisterRequest {
    pub name: String,
    pub capabilities: Vec<WorkerCapability>,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct RegisterResponse {
    pub agent_id: Uuid,
    pub token: String,
    pub config_url: String,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct HeartbeatRequest {
    pub agent_id: Uuid,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct HeartbeatResponse {
    pub status: String,
    pub last_heartbeat: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct ClaimRequest {
    pub agent_id: Uuid,
    pub capabilities: Vec<WorkerCapability>,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct ClaimResponse {
    pub job_id: Uuid,
    pub job_run_id: Uuid,
    pub source_id: Uuid,
    pub source: serde_json::Value,
    pub config: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_item: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct ProgressRequest {
    pub agent_id: Uuid,
    pub job_run_id: Uuid,
    #[serde(default)]
    pub message: Option<String>,
    #[serde(default)]
    pub details: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct CompleteRequest {
    pub agent_id: Uuid,
    pub job_run_id: Uuid,
    #[serde(default)]
    pub artifacts: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct FailRequest {
    pub agent_id: Uuid,
    pub job_run_id: Uuid,
    pub error: String,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct CreateSourceItemDto {
    pub fingerprint: String,
    #[serde(default)]
    pub provenance: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct CreateItemsRequest {
    pub agent_id: Uuid,
    pub items: Vec<CreateSourceItemDto>,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct CreateItemsResponse {
    pub items: Vec<SourceItem>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct IndexChunksRequest {
    pub agent_id: Uuid,
    pub chunks: Vec<chunk_index::ChunkInput>,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct GetArtifactsQuery {
    pub job_kind: WorkerCapability,
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct CreateJobRequest {
    pub agent_id: Uuid,
    pub source_id: Uuid,
    pub source_item_id: Uuid,
    pub job_kind: WorkerCapability,
}

// --- Handlers ---

#[utoipa::path(
    post,
    path = "/workers/register",
    request_body = RegisterRequest,
    responses((status = 200, body = RegisterResponse), (status = 400))
)]
pub async fn register(
    State(state): State<Arc<AppState>>,
    Json(req): Json<RegisterRequest>,
) -> Result<Json<RegisterResponse>, ApiError> {
    let result = workers::register(
        &state.pool,
        workers::RegisterInput {
            name: req.name,
            capabilities: req.capabilities,
        },
    )
    .await?;
    Ok(Json(RegisterResponse {
        agent_id: result.agent.id,
        token: result.token,
        config_url: "/api/workers/config".to_string(),
    }))
}

#[utoipa::path(
    post,
    path = "/workers/heartbeat",
    request_body = HeartbeatRequest,
    responses((status = 200, body = HeartbeatResponse), (status = 404))
)]
pub async fn heartbeat(
    State(state): State<Arc<AppState>>,
    Json(req): Json<HeartbeatRequest>,
) -> Result<Json<HeartbeatResponse>, ApiError> {
    let agent = workers::heartbeat(&state.pool, req.agent_id).await?;
    Ok(Json(HeartbeatResponse {
        status: format!("{:?}", agent.status).to_lowercase(),
        last_heartbeat: agent.last_heartbeat,
    }))
}

#[utoipa::path(
    post,
    path = "/workers/jobs/claim",
    request_body = ClaimRequest,
    responses((status = 200, body = ClaimResponse), (status = 204), (status = 400))
)]
pub async fn claim(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ClaimRequest>,
) -> Result<axum::response::Response, ApiError> {
    let result = workers::claim(&state.pool, req.agent_id, &req.capabilities).await?;
    match result {
        Some(claim) => {
            let source_json = serde_json::json!({
                "id": claim.source.id,
                "name": claim.source.name,
                "kind": format!("{:?}", claim.source.kind).to_lowercase(),
                "config": claim.source.config,
            });
            let source_item_json = claim.source_item.map(|si| {
                serde_json::json!({
                    "id": si.id,
                    "source_id": si.source_id,
                    "fingerprint": si.fingerprint,
                    "provenance": si.provenance,
                })
            });
            Ok(axum::Json(ClaimResponse {
                job_id: claim.job.id,
                job_run_id: claim.job_run_id,
                source_id: claim.source.id,
                source: source_json,
                config: claim.source.config.clone(),
                source_item: source_item_json,
            })
            .into_response())
        }
        None => Ok(axum::http::StatusCode::NO_CONTENT.into_response()),
    }
}

#[utoipa::path(
    post,
    path = "/workers/jobs/{job_id}/progress",
    request_body = ProgressRequest,
    responses((status = 200), (status = 403), (status = 404), (status = 409))
)]
pub async fn progress(
    State(state): State<Arc<AppState>>,
    Path(id): Path<Uuid>,
    Json(req): Json<ProgressRequest>,
) -> Result<axum::http::StatusCode, ApiError> {
    workers::progress(
        &state.pool,
        req.agent_id,
        id,
        req.job_run_id,
        workers::ProgressInput {
            message: req.message,
            details: req.details,
        },
    )
    .await?;
    Ok(axum::http::StatusCode::OK)
}

#[utoipa::path(
    post,
    path = "/workers/jobs/{job_id}/complete",
    request_body = CompleteRequest,
    responses((status = 200), (status = 403), (status = 404), (status = 409))
)]
pub async fn complete(
    State(state): State<Arc<AppState>>,
    Path(id): Path<Uuid>,
    Json(req): Json<CompleteRequest>,
) -> Result<axum::http::StatusCode, ApiError> {
    workers::complete(
        &state.pool,
        req.agent_id,
        id,
        req.job_run_id,
        workers::CompleteInput {
            artifacts: req.artifacts,
        },
    )
    .await?;
    Ok(axum::http::StatusCode::OK)
}

#[utoipa::path(
    post,
    path = "/workers/jobs/{job_id}/fail",
    request_body = FailRequest,
    responses((status = 200), (status = 403), (status = 404), (status = 409))
)]
pub async fn fail(
    State(state): State<Arc<AppState>>,
    Path(id): Path<Uuid>,
    Json(req): Json<FailRequest>,
) -> Result<axum::http::StatusCode, ApiError> {
    workers::fail(
        &state.pool,
        req.agent_id,
        id,
        req.job_run_id,
        workers::FailInput { error: req.error },
    )
    .await?;
    Ok(axum::http::StatusCode::OK)
}

#[utoipa::path(
    post,
    path = "/workers/sources/{source_id}/items",
    request_body = CreateItemsRequest,
    responses((status = 200, body = CreateItemsResponse), (status = 400), (status = 404))
)]
pub async fn create_items(
    State(state): State<Arc<AppState>>,
    Path(source_id): Path<Uuid>,
    Json(req): Json<CreateItemsRequest>,
) -> Result<Json<CreateItemsResponse>, ApiError> {
    let _agent = crate::services::agents::get(&state.pool, req.agent_id).await?;
    let _source = crate::services::sources::get(&state.pool, source_id).await?;
    let items: Vec<source_items::CreateSourceItem> = req
        .items
        .into_iter()
        .map(|i| source_items::CreateSourceItem {
            fingerprint: i.fingerprint,
            provenance: i.provenance,
        })
        .collect();
    let created = source_items::create_batch(&state.pool, source_id, items).await?;
    Ok(Json(CreateItemsResponse { items: created }))
}

#[utoipa::path(
    post,
    path = "/workers/jobs",
    request_body = CreateJobRequest,
    responses((status = 201, body = crate::entities::Job), (status = 400), (status = 404))
)]
pub async fn create_job(
    State(state): State<Arc<AppState>>,
    Json(req): Json<CreateJobRequest>,
) -> Result<(axum::http::StatusCode, Json<crate::entities::Job>), ApiError> {
    if !matches!(
        req.job_kind,
        WorkerCapability::Docproc
            | WorkerCapability::Image
            | WorkerCapability::Ocr
            | WorkerCapability::Enrich
            | WorkerCapability::Embed
    ) {
        return Err(ApiError::BadRequest(
            "job_kind must be docproc, image, ocr, enrich, or embed".into(),
        ));
    }
    let _agent = crate::services::agents::get(&state.pool, req.agent_id).await?;
    let _source = crate::services::sources::get(&state.pool, req.source_id).await?;
    let job = jobs::create_for_item(
        &state.pool,
        req.source_id,
        req.source_item_id,
        req.job_kind,
    )
    .await?;
    Ok((axum::http::StatusCode::CREATED, Json(job)))
}

#[utoipa::path(
    get,
    path = "/workers/source-items/{id}/artifacts",
    params(("id" = Uuid, Path, description = "Source item ID"), ("job_kind" = WorkerCapability, Query)),
    responses((status = 200, description = "Artifacts from latest completed job"), (status = 404))
)]
pub async fn get_source_item_artifacts(
    State(state): State<Arc<AppState>>,
    Path(id): Path<Uuid>,
    Query(query): Query<GetArtifactsQuery>,
) -> Result<axum::response::Response, ApiError> {
    let artifacts = workers::get_artifacts_for_source_item(
        &state.pool,
        id,
        query.job_kind,
    )
    .await?;
    match artifacts {
        Some(a) => Ok(Json(a).into_response()),
        None => Ok(axum::http::StatusCode::NOT_FOUND.into_response()),
    }
}

#[utoipa::path(
    post,
    path = "/workers/source-items/{id}/index-chunks",
    params(("id" = Uuid, Path, description = "Source item ID")),
    request_body = IndexChunksRequest,
    responses((status = 200), (status = 400), (status = 404))
)]
pub async fn index_chunks(
    State(state): State<Arc<AppState>>,
    Path(id): Path<Uuid>,
    Json(req): Json<IndexChunksRequest>,
) -> Result<axum::response::Response, ApiError> {
    let _agent = crate::services::agents::get(&state.pool, req.agent_id).await?;
    let si = source_items::get(&state.pool, id).await?;
    let src = sources::get(&state.pool, si.source_id).await?;
    let count = chunk_index::upsert_chunks(
        &state.pool,
        si.id,
        si.source_id,
        src.workspace_id,
        req.chunks,
    )
    .await?;
    Ok(Json(serde_json::json!({ "indexed": count })).into_response())
}
