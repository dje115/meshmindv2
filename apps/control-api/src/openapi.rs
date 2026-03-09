//! OpenAPI spec generation.

use utoipa::OpenApi;

#[derive(OpenApi)]
#[openapi(
    paths(
        crate::api::handlers::health_handler,
        crate::api::handlers::ready,
        crate::api::handlers::login,
        crate::api::handlers::me,
        crate::api::workers::register,
        crate::api::workers::heartbeat,
        crate::api::workers::claim,
        crate::api::workers::progress,
        crate::api::workers::complete,
        crate::api::workers::fail,
    ),
    components(schemas(
        crate::api::handlers::HealthResponse,
        crate::api::handlers::ReadyResponse,
        crate::api::handlers::LoginRequest,
        crate::api::handlers::LoginResponse,
        crate::api::handlers::UserResponse,
        crate::api::workers::RegisterRequest,
        crate::api::workers::RegisterResponse,
        crate::api::workers::HeartbeatRequest,
        crate::api::workers::HeartbeatResponse,
        crate::api::workers::ClaimRequest,
        crate::api::workers::ClaimResponse,
        crate::api::workers::ProgressRequest,
        crate::api::workers::CompleteRequest,
        crate::api::workers::FailRequest,
        crate::entities::WorkerCapability,
    ))
)]
pub struct ApiDoc;
