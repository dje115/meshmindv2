//! JWT-based auth for on-prem deployment.

use crate::error::ApiError;
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{header, request::Parts, StatusCode},
};
use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// JWT claims.
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,       // user_id
    pub username: String,
    pub exp: i64,
    pub iat: i64,
}

/// Auth config.
#[derive(Clone)]
pub struct AuthConfig {
    pub jwt_secret: Vec<u8>,
    pub jwt_ttl_secs: i64,
}

impl AuthConfig {
    pub fn from_secret(secret: &str) -> Self {
        Self {
            jwt_secret: secret.as_bytes().to_vec(),
            jwt_ttl_secs: 86400, // 24h
        }
    }

    pub fn create_token(&self, user_id: Uuid, username: &str) -> Result<String, ApiError> {
        let now = Utc::now();
        let exp = now + Duration::seconds(self.jwt_ttl_secs);
        let claims = Claims {
            sub: user_id.to_string(),
            username: username.to_string(),
            exp: exp.timestamp(),
            iat: now.timestamp(),
        };
        encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(&self.jwt_secret),
        )
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("JWT encode: {}", e)))
    }

    pub fn verify_token(&self, token: &str) -> Result<Claims, ApiError> {
        let data = decode::<Claims>(
            token,
            &DecodingKey::from_secret(&self.jwt_secret),
            &Validation::default(),
        )
        .map_err(|_| ApiError::Unauthorized("invalid or expired token".into()))?;
        Ok(data.claims)
    }
}

/// Authenticated user extractor.
pub struct AuthUser {
    pub user_id: Uuid,
    pub username: String,
    pub claims: Claims,
}

#[async_trait]
impl<S> FromRequestParts<S> for AuthUser
where
    S: Send + Sync,
{
    type Rejection = (StatusCode, String);

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        let auth = parts
            .headers
            .get(header::AUTHORIZATION)
            .and_then(|v| v.to_str().ok())
            .and_then(|v| v.strip_prefix("Bearer "));

        let token = auth.ok_or_else(|| {
            (
                StatusCode::UNAUTHORIZED,
                "missing or invalid Authorization header".to_string(),
            )
        })?;

        let config = parts
            .extensions
            .get::<AuthConfig>()
            .cloned()
            .ok_or_else(|| {
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "auth not configured".to_string(),
                )
            })?;

        let claims = config.verify_token(token).map_err(|e| {
            (
                e.status(),
                e.message(),
            )
        })?;

        let user_id = Uuid::parse_str(&claims.sub).map_err(|_| {
            (
                StatusCode::UNAUTHORIZED,
                "invalid token sub".to_string(),
            )
        })?;

        Ok(AuthUser {
            user_id,
            username: claims.username.clone(),
            claims,
        })
    }
}
