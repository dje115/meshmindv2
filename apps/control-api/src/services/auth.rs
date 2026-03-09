//! Auth service (login, token).

use crate::auth::AuthConfig;
use crate::entities::User;
use crate::error::ApiError;
use argon2::{Argon2, PasswordHash, PasswordVerifier};
use sqlx::PgPool;
use uuid::Uuid;

pub async fn login(
    pool: &PgPool,
    auth_config: &AuthConfig,
    username: &str,
    password: &str,
) -> Result<(User, String), ApiError> {
    let user = sqlx::query_as::<_, User>(
        r#"SELECT id, username, password_hash, email, display_name, created_at, updated_at FROM users WHERE username = $1"#,
    )
    .bind(username)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("login query: {}", e)))?
    .ok_or_else(|| ApiError::Unauthorized("invalid username or password".into()))?;

    let hash = user
        .password_hash
        .as_ref()
        .ok_or_else(|| ApiError::Unauthorized("invalid username or password".into()))?;
    let parsed = PasswordHash::new(hash)
        .map_err(|_| ApiError::Unauthorized("invalid username or password".into()))?;
    Argon2::default()
        .verify_password(password.as_bytes(), &parsed)
        .map_err(|_| ApiError::Unauthorized("invalid username or password".into()))?;

    let token = auth_config.create_token(user.id, &user.username)?;
    Ok((user, token))
}
