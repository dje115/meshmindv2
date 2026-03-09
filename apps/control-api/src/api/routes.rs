//! Route definitions.

use super::handlers::{self, AppState};
use super::workers;
use axum::{
    middleware,
    routing::{delete, get, post, put},
    Router,
};
use std::sync::Arc;
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

pub fn router(state: Arc<AppState>) -> Router {
    let worker_routes = Router::new()
        .route("/register", post(workers::register))
        .route("/heartbeat", post(workers::heartbeat))
        .route("/sources/:source_id/items", post(workers::create_items))
        .route("/jobs", post(workers::create_job))
        .route("/jobs/claim", post(workers::claim))
        .route("/jobs/{id}/progress", post(workers::progress))
        .route("/jobs/{id}/complete", post(workers::complete))
        .route("/jobs/{id}/fail", post(workers::fail));

    let api = Router::new()
        .nest("/workers", worker_routes)
        .route("/health", get(handlers::health_handler))
        .route("/ready", get(handlers::ready))
        .route("/auth/login", post(handlers::login))
        .route("/me", get(handlers::me))
        .route("/workspaces", get(handlers::workspaces_list).post(handlers::workspaces_create))
        .route(
            "/workspaces/:id",
            get(handlers::workspaces_get)
                .put(handlers::workspaces_update)
                .delete(handlers::workspaces_delete),
        )
        .route("/roles", get(handlers::roles_list).post(handlers::roles_create))
        .route(
            "/roles/:id",
            get(handlers::roles_get)
                .put(handlers::roles_update)
                .delete(handlers::roles_delete),
        )
        .route("/users", get(handlers::users_list).post(handlers::users_create))
        .route(
            "/users/:id",
            get(handlers::users_get)
                .put(handlers::users_update)
                .delete(handlers::users_delete),
        )
        .route("/sources", get(handlers::sources_list).post(handlers::sources_create))
        .route(
            "/sources/:id",
            get(handlers::sources_get)
                .put(handlers::sources_update)
                .delete(handlers::sources_delete),
        )
        .route("/agents", get(handlers::agents_list))
        .route("/jobs", get(handlers::jobs_list))
        .route("/audit", get(handlers::audit_list))
        .route_layer(middleware::from_fn_with_state(
            state.clone(),
            crate::middleware::request_id_and_extensions,
        ))
        .with_state(state);

    let openapi = crate::openapi::ApiDoc::openapi();
    Router::new()
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", openapi.clone()))
        .nest("/api", api)
}
