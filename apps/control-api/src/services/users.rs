//! User service.

use crate::entities::User;
use crate::error::ApiError;
use argon2::{
    password_hash::{rand_core::OsRng, PasswordHasher, SaltString},
    Argon2,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct CreateUser {
    pub username: String,
    pub password: String,
    pub email: Option<String>,
    pub display_name: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateUser {
    pub email: Option<String>,
    pub display_name: Option<String>,
}

pub async fn list(pool: &PgPool) -> Result<Vec<User>, ApiError> {
    let users = sqlx::query_as::<_, User>(
        r#"SELECT id, username, NULL as password_hash, email, display_name, created_at, updated_at FROM users ORDER BY username"#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("users list: {}", e)))?;
    Ok(users)
}

pub async fn get(pool: &PgPool, id: Uuid) -> Result<User, ApiError> {
    let user = sqlx::query_as::<_, User>(
        r#"SELECT id, username, NULL as password_hash, email, display_name, created_at, updated_at FROM users WHERE id = $1"#,
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("user get: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("user not found".into()))?;
    Ok(user)
}

pub async fn get_by_username(pool: &PgPool, username: &str) -> Result<User, ApiError> {
    let user = sqlx::query_as::<_, User>(
        r#"SELECT id, username, NULL as password_hash, email, display_name, created_at, updated_at FROM users WHERE username = $1"#,
    )
    .bind(username)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("user get: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("user not found".into()))?;
    Ok(user)
}

pub async fn create(pool: &PgPool, input: CreateUser) -> Result<User, ApiError> {
    let salt = SaltString::generate(&mut OsRng);
    let hash = Argon2::default()
        .hash_password(input.password.as_bytes(), &salt)
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("hash: {}", e)))?
        .to_string();

    let id = Uuid::new_v4();
    let user = sqlx::query_as::<_, User>(
        r#"
        INSERT INTO users (id, username, password_hash, email, display_name)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, username, NULL as password_hash, email, display_name, created_at, updated_at
        "#,
    )
    .bind(id)
    .bind(&input.username)
    .bind(&hash)
    .bind(&input.email)
    .bind(&input.display_name)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        if let Some(db_err) = e.as_database_error() {
            if db_err.constraint().is_some() {
                return ApiError::Conflict("username already exists".into());
            }
        }
        ApiError::Internal(anyhow::anyhow!("user create: {}", e))
    })?;
    Ok(user)
}

pub async fn update(pool: &PgPool, id: Uuid, input: UpdateUser) -> Result<User, ApiError> {
    let user = sqlx::query_as::<_, User>(
        r#"
        UPDATE users SET email = COALESCE($2, email), display_name = COALESCE($3, display_name), updated_at = now()
        WHERE id = $1
        RETURNING id, username, NULL as password_hash, email, display_name, created_at, updated_at
        "#,
    )
    .bind(id)
    .bind(&input.email)
    .bind(&input.display_name)
    .fetch_optional(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("user update: {}", e)))?
    .ok_or_else(|| ApiError::NotFound("user not found".into()))?;
    Ok(user)
}

pub async fn delete(pool: &PgPool, id: Uuid) -> Result<(), ApiError> {
    let r = sqlx::query(r#"DELETE FROM users WHERE id = $1"#)
        .bind(id)
        .execute(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("user delete: {}", e)))?;
    if r.rows_affected() == 0 {
        return Err(ApiError::NotFound("user not found".into()));
    }
    Ok(())
}
