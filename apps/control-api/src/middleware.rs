//! Request ID and extensions middleware.

use crate::api::handlers::AppState;
use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};
use std::sync::Arc;
use uuid::Uuid;

/// Request ID header name.
pub const REQUEST_ID_HEADER: &str = "x-request-id";
pub const REQUEST_ID_RESPONSE_HEADER: &str = "x-request-id";

/// Add request ID and auth config to extensions.
pub async fn request_id_and_extensions(
    axum::extract::State(state): axum::extract::State<Arc<AppState>>,
    mut req: Request,
    next: Next,
) -> Response {
    let request_id = req
        .headers()
        .get(REQUEST_ID_HEADER)
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string())
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    req.extensions_mut().insert(state.auth_config.clone());
    req.extensions_mut().insert(RequestId(request_id.clone()));

    let mut res = next.run(req).await;

    let _ = res.headers_mut().insert(
        REQUEST_ID_RESPONSE_HEADER,
        request_id
            .parse()
            .unwrap_or_else(|_| "unknown".parse().unwrap()),
    );

    res
}

/// Request ID extractor.
#[derive(Clone)]
pub struct RequestId(pub String);

impl RequestId {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}
