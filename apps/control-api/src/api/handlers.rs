//! Request handlers.

use crate::audit;
use crate::auth::{AuthConfig, AuthUser};
use crate::entities::*;
use crate::error::ApiError;
use crate::services;
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    Json,
};
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;
use std::sync::Arc;
use uuid::Uuid;

#[derive(Clone)]
pub struct AppState {
    pub pool: sqlx::PgPool,
    pub auth_config: AuthConfig,
    pub query_api_url: String,
    pub ollama_url: String,
    pub qdrant_url: String,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct HealthResponse {
    pub status: &'static str,
    pub version: &'static str,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct ReadyResponse {
    pub status: &'static str,
    pub database: &'static str,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct LoginResponse {
    pub token: String,
    pub user: UserResponse,
}

#[derive(Debug, Serialize, ToSchema)]
pub struct UserResponse {
    pub id: Uuid,
    pub username: String,
    pub email: Option<String>,
    pub display_name: Option<String>,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

impl From<User> for UserResponse {
    fn from(u: User) -> Self {
        Self {
            id: u.id,
            username: u.username,
            email: u.email,
            display_name: u.display_name,
            created_at: u.created_at,
        }
    }
}

#[derive(Debug, Deserialize, ToSchema)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
}

// --- Health ---
pub fn health_response() -> HealthResponse {
    HealthResponse {
        status: "ok",
        version: env!("CARGO_PKG_VERSION"),
    }
}

#[utoipa::path(get, path = "/health", responses((status = 200, body = HealthResponse)))]
pub async fn health_handler() -> Json<HealthResponse> {
    Json(health_response())
}

#[utoipa::path(get, path = "/ready", responses((status = 200, body = ReadyResponse)))]
pub async fn ready(State(state): State<Arc<AppState>>) -> Result<Json<ReadyResponse>, ApiError> {
    sqlx::query("SELECT 1")
        .execute(&state.pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("db: {}", e)))?;
    Ok(Json(ReadyResponse {
        status: "ok",
        database: "connected",
    }))
}

// --- Auth ---
#[utoipa::path(
    post,
    path = "/auth/login",
    request_body = LoginRequest,
    responses((status = 200, body = LoginResponse), (status = 401))
)]
pub async fn login(
    State(state): State<Arc<AppState>>,
    Json(req): Json<LoginRequest>,
) -> Result<Json<LoginResponse>, ApiError> {
    let (user, token) =
        services::auth::login(&state.pool, &state.auth_config, &req.username, &req.password).await?;
    Ok(Json(LoginResponse {
        token,
        user: user.into(),
    }))
}

#[utoipa::path(get, path = "/me", responses((status = 200, body = UserResponse), (status = 401)))]
pub async fn me(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
) -> Result<Json<UserResponse>, ApiError> {
    let user = services::users::get(&state.pool, auth.user_id).await?;
    Ok(Json(user.into()))
}

// --- Workspaces ---
#[derive(Debug, Deserialize)]
pub struct CreateWorkspaceRequest {
    pub name: String,
    pub slug: String,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateWorkspaceRequest {
    pub name: Option<String>,
    pub slug: Option<String>,
    pub description: Option<String>,
}

pub async fn workspaces_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
) -> Result<Json<Vec<Workspace>>, ApiError> {
    let list = services::workspaces::list(&state.pool).await?;
    Ok(Json(list))
}

pub async fn workspaces_create(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Json(req): Json<CreateWorkspaceRequest>,
) -> Result<(StatusCode, Json<Workspace>), ApiError> {
    let ws = services::workspaces::create(
        &state.pool,
        services::workspaces::CreateWorkspace {
            name: req.name,
            slug: req.slug,
            description: req.description,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "workspace.create",
        "workspace",
        Some(ws.id),
        None,
        serde_json::json!({ "name": ws.name }),
    )
    .await?;
    Ok((StatusCode::CREATED, Json(ws)))
}

pub async fn workspaces_get(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<Json<Workspace>, ApiError> {
    let ws = services::workspaces::get(&state.pool, id).await?;
    Ok(Json(ws))
}

pub async fn workspaces_update(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
    Json(req): Json<UpdateWorkspaceRequest>,
) -> Result<Json<Workspace>, ApiError> {
    let ws = services::workspaces::update(
        &state.pool,
        id,
        services::workspaces::UpdateWorkspace {
            name: req.name,
            slug: req.slug,
            description: req.description,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        Some(ws.id),
        Some(auth.user_id),
        "workspace.update",
        "workspace",
        Some(ws.id),
        None,
        serde_json::json!({ "name": ws.name }),
    )
    .await?;
    Ok(Json(ws))
}

pub async fn workspaces_delete(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, ApiError> {
    services::workspaces::delete(&state.pool, id).await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "workspace.delete",
        "workspace",
        Some(id),
        None,
        serde_json::json!({}),
    )
    .await?;
    Ok(StatusCode::NO_CONTENT)
}

// --- Roles ---
#[derive(Debug, Deserialize)]
pub struct CreateRoleRequest {
    pub name: String,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateRoleRequest {
    pub description: Option<String>,
}

pub async fn roles_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
) -> Result<Json<Vec<Role>>, ApiError> {
    let list = services::roles::list(&state.pool).await?;
    Ok(Json(list))
}

pub async fn roles_create(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Json(req): Json<CreateRoleRequest>,
) -> Result<(StatusCode, Json<Role>), ApiError> {
    let role = services::roles::create(
        &state.pool,
        services::roles::CreateRole {
            name: req.name,
            description: req.description,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "role.create",
        "role",
        Some(role.id),
        None,
        serde_json::json!({ "name": role.name }),
    )
    .await?;
    Ok((StatusCode::CREATED, Json(role)))
}

pub async fn roles_get(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<Json<Role>, ApiError> {
    let role = services::roles::get(&state.pool, id).await?;
    Ok(Json(role))
}

pub async fn roles_update(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
    Json(req): Json<UpdateRoleRequest>,
) -> Result<Json<Role>, ApiError> {
    let role = services::roles::update(&state.pool, id, services::roles::UpdateRole { description: req.description })
        .await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "role.update",
        "role",
        Some(role.id),
        None,
        serde_json::json!({ "name": role.name }),
    )
    .await?;
    Ok(Json(role))
}

pub async fn roles_delete(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, ApiError> {
    services::roles::delete(&state.pool, id).await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "role.delete",
        "role",
        Some(id),
        None,
        serde_json::json!({}),
    )
    .await?;
    Ok(StatusCode::NO_CONTENT)
}

// --- Users ---
#[derive(Debug, Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub password: String,
    pub email: Option<String>,
    pub display_name: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateUserRequest {
    pub email: Option<String>,
    pub display_name: Option<String>,
}

pub async fn users_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
) -> Result<Json<Vec<User>>, ApiError> {
    let list = services::users::list(&state.pool).await?;
    Ok(Json(list))
}

pub async fn users_create(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Json(req): Json<CreateUserRequest>,
) -> Result<(StatusCode, Json<User>), ApiError> {
    let user = services::users::create(
        &state.pool,
        services::users::CreateUser {
            username: req.username,
            password: req.password,
            email: req.email,
            display_name: req.display_name,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "user.create",
        "user",
        Some(user.id),
        None,
        serde_json::json!({ "username": user.username }),
    )
    .await?;
    Ok((StatusCode::CREATED, Json(user)))
}

pub async fn users_get(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<Json<User>, ApiError> {
    let user = services::users::get(&state.pool, id).await?;
    Ok(Json(user))
}

pub async fn users_update(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
    Json(req): Json<UpdateUserRequest>,
) -> Result<Json<User>, ApiError> {
    let user = services::users::update(
        &state.pool,
        id,
        services::users::UpdateUser {
            email: req.email,
            display_name: req.display_name,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "user.update",
        "user",
        Some(user.id),
        None,
        serde_json::json!({ "username": user.username }),
    )
    .await?;
    Ok(Json(user))
}

pub async fn users_delete(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, ApiError> {
    services::users::delete(&state.pool, id).await?;
    audit::create(
        &state.pool,
        None,
        Some(auth.user_id),
        "user.delete",
        "user",
        Some(id),
        None,
        serde_json::json!({}),
    )
    .await?;
    Ok(StatusCode::NO_CONTENT)
}

// --- Sources ---
#[derive(Debug, Deserialize)]
pub struct CreateSourceRequest {
    pub workspace_id: Uuid,
    pub name: String,
    pub kind: SourceKind,
    pub config: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateSourceRequest {
    pub name: Option<String>,
    pub kind: Option<SourceKind>,
    pub config: Option<serde_json::Value>,
    pub status: Option<SourceStatus>,
}

pub async fn sources_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Query(q): Query<SourcesListQuery>,
) -> Result<Json<Vec<Source>>, ApiError> {
    let list = services::sources::list(&state.pool, q.workspace_id).await?;
    Ok(Json(list))
}

#[derive(Debug, Deserialize)]
pub struct SourcesListQuery {
    pub workspace_id: Option<Uuid>,
}

pub async fn sources_create(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Json(req): Json<CreateSourceRequest>,
) -> Result<(StatusCode, Json<Source>), ApiError> {
    let source = services::sources::create(
        &state.pool,
        services::sources::CreateSource {
            workspace_id: req.workspace_id,
            name: req.name,
            kind: req.kind,
            config: req.config,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        Some(source.workspace_id),
        Some(auth.user_id),
        "source.create",
        "source",
        Some(source.id),
        None,
        serde_json::json!({ "name": source.name }),
    )
    .await?;
    Ok((StatusCode::CREATED, Json(source)))
}

pub async fn sources_get(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<Json<Source>, ApiError> {
    let source = services::sources::get(&state.pool, id).await?;
    Ok(Json(source))
}

pub async fn sources_update(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
    Json(req): Json<UpdateSourceRequest>,
) -> Result<Json<Source>, ApiError> {
    let source = services::sources::update(
        &state.pool,
        id,
        services::sources::UpdateSource {
            name: req.name,
            kind: req.kind,
            config: req.config,
            status: req.status,
        },
    )
    .await?;
    audit::create(
        &state.pool,
        Some(source.workspace_id),
        Some(auth.user_id),
        "source.update",
        "source",
        Some(source.id),
        None,
        serde_json::json!({ "name": source.name }),
    )
    .await?;
    Ok(Json(source))
}

pub async fn sources_ingest(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<(StatusCode, Json<Job>), ApiError> {
    let has = services::permissions::user_has_permission(&state.pool, auth.user_id, "sources:ingest").await?;
    if !has {
        return Err(ApiError::Forbidden("sources:ingest permission required".into()));
    }
    let source = services::sources::get(&state.pool, id).await?;
    let job = services::jobs::create(&state.pool, id).await?;
    audit::create(
        &state.pool,
        Some(source.workspace_id),
        Some(auth.user_id),
        "source.ingest",
        "source",
        Some(id),
        None,
        serde_json::json!({ "job_id": job.id }),
    )
    .await?;
    Ok((StatusCode::CREATED, Json(job)))
}

pub async fn sources_delete(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, ApiError> {
    let source = services::sources::get(&state.pool, id).await?;
    services::sources::delete(&state.pool, id).await?;
    audit::create(
        &state.pool,
        Some(source.workspace_id),
        Some(auth.user_id),
        "source.delete",
        "source",
        Some(id),
        None,
        serde_json::json!({}),
    )
    .await?;
    Ok(StatusCode::NO_CONTENT)
}

// --- Agents ---
#[derive(Debug, Deserialize)]
pub struct AgentsListQuery {
    pub status: Option<String>,
}

pub async fn agents_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Query(q): Query<AgentsListQuery>,
) -> Result<Json<Vec<Agent>>, ApiError> {
    let list = services::agents::list(&state.pool, q.status.as_deref()).await?;
    Ok(Json(list))
}

// --- Jobs ---
#[derive(Debug, Deserialize)]
pub struct JobsListQuery {
    pub source_id: Option<Uuid>,
    pub status: Option<String>,
    #[serde(default = "default_limit")]
    pub limit: i64,
}

fn default_limit() -> i64 {
    20
}

pub async fn jobs_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Query(q): Query<JobsListQuery>,
) -> Result<Json<Vec<Job>>, ApiError> {
    let list = services::jobs::list(&state.pool, q.source_id, q.status.as_deref(), q.limit).await?;
    Ok(Json(list))
}

pub async fn jobs_reset_stuck(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
) -> Result<Json<serde_json::Value>, ApiError> {
    let count = services::jobs::reset_stuck_claimed(&state.pool).await?;
    Ok(Json(serde_json::json!({ "reset": count })))
}

// --- Audit ---
#[derive(Debug, Deserialize)]
pub struct AuditListQuery {
    pub workspace_id: Option<Uuid>,
    pub user_id: Option<Uuid>,
    #[serde(default = "default_audit_limit")]
    pub limit: i64,
}

fn default_audit_limit() -> i64 {
    50
}

pub async fn audit_list(
    State(state): State<Arc<AppState>>,
    _auth: AuthUser,
    Query(q): Query<AuditListQuery>,
) -> Result<Json<Vec<AuditEvent>>, ApiError> {
    let list = services::audit_events::list(&state.pool, q.workspace_id, q.user_id, q.limit).await?;
    Ok(Json(list))
}

// --- Components status ---
#[derive(Debug, Serialize)]
pub struct ComponentStatus {
    pub status: &'static str,
    pub message: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ComponentsStatusResponse {
    pub control_api: ComponentStatus,
    pub database: ComponentStatus,
    pub query_api: ComponentStatus,
    pub ollama: ComponentStatus,
    pub qdrant: ComponentStatus,
}

pub async fn components_status(State(state): State<Arc<AppState>>) -> Result<Json<ComponentsStatusResponse>, ApiError> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("http client: {}", e)))?;

    let (db_ok, db_err) = match sqlx::query("SELECT 1").execute(&state.pool).await {
        Ok(_) => ("ok", None),
        Err(e) => ("error", Some(e.to_string())),
    };

    let query_url = format!("{}/health", state.query_api_url.trim_end_matches('/'));
    let query_fut = client.get(&query_url).send();
    let ollama_url = format!("{}/api/version", state.ollama_url.trim_end_matches('/'));
    let ollama_fut = client.get(&ollama_url).send();
    let qdrant_url = format!("{}/", state.qdrant_url.trim_end_matches('/'));
    let qdrant_fut = client.get(&qdrant_url).send();

    let (query_res, ollama_res, qdrant_res) =
        tokio::join!(query_fut, ollama_fut, qdrant_fut);

    let (query_ok, query_err) = match query_res {
        Ok(r) if r.status().is_success() => ("ok", None),
        Ok(r) => ("error", Some(format!("HTTP {}", r.status()))),
        Err(e) => ("error", Some(e.to_string())),
    };
    let (ollama_ok, ollama_err) = match ollama_res {
        Ok(r) if r.status().is_success() => ("ok", None),
        Ok(r) => ("error", Some(format!("HTTP {}", r.status()))),
        Err(e) => ("error", Some(e.to_string())),
    };
    let (qdrant_ok, qdrant_err) = match qdrant_res {
        Ok(r) if r.status().is_success() => ("ok", None),
        Ok(r) => ("error", Some(format!("HTTP {}", r.status()))),
        Err(e) => ("error", Some(e.to_string())),
    };

    Ok(Json(ComponentsStatusResponse {
        control_api: ComponentStatus {
            status: "ok",
            message: None,
        },
        database: ComponentStatus {
            status: db_ok,
            message: db_err,
        },
        query_api: ComponentStatus {
            status: query_ok,
            message: query_err,
        },
        ollama: ComponentStatus {
            status: ollama_ok,
            message: ollama_err,
        },
        qdrant: ComponentStatus {
            status: qdrant_ok,
            message: qdrant_err,
        },
    }))
}

// --- Settings ---
pub async fn settings_get(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
) -> Result<Json<serde_json::Value>, ApiError> {
    let has = services::permissions::user_has_permission(&state.pool, auth.user_id, "settings:read").await?;
    if !has {
        return Err(ApiError::Forbidden("settings:read permission required".into()));
    }
    let all = services::app_settings::get_all(&state.pool).await?;
    let obj: serde_json::Map<String, serde_json::Value> = all
        .into_iter()
        .map(|(k, v)| {
            let obj: serde_json::Map<String, serde_json::Value> = v.into_iter().collect();
            (k, serde_json::Value::Object(obj))
        })
        .collect();
    Ok(Json(serde_json::Value::Object(obj)))
}

#[derive(Debug, Deserialize)]
pub struct SettingsUpdateRequest {
    pub category: String,
    pub settings: std::collections::HashMap<String, serde_json::Value>,
}

pub async fn settings_update(
    State(state): State<Arc<AppState>>,
    auth: AuthUser,
    Json(req): Json<SettingsUpdateRequest>,
) -> Result<Json<serde_json::Value>, ApiError> {
    let has = services::permissions::user_has_permission(&state.pool, auth.user_id, "settings:write").await?;
    if !has {
        return Err(ApiError::Forbidden("settings:write permission required".into()));
    }
    services::app_settings::set_category(&state.pool, &req.category, &req.settings).await?;
    let updated = services::app_settings::get_category(&state.pool, &req.category).await?;
    let obj: serde_json::Map<String, serde_json::Value> = updated.into_iter().collect();
    Ok(Json(serde_json::Value::Object(obj)))
}
