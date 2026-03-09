//! Database pool and migrations.

use crate::config::Config;
use crate::error::ApiError;
use argon2::{
    password_hash::{rand_core::OsRng, PasswordHasher, SaltString},
    Argon2,
};
use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use std::time::Duration;
use uuid::Uuid;

/// Run migrations.
pub async fn migrate(pool: &PgPool) -> Result<(), ApiError> {
    sqlx::migrate!("./migrations")
        .run(pool)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("migration: {}", e)))?;
    Ok(())
}

/// Create pool from config.
pub async fn create_pool(config: &Config) -> Result<PgPool, ApiError> {
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .acquire_timeout(Duration::from_secs(5))
        .connect(&config.database_url)
        .await
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("db connect: {}", e)))?;
    Ok(pool)
}

/// Seed dev admin user if MESHMIND_SEED_DEV_ADMIN=true.
pub async fn seed_dev_admin(pool: &PgPool) -> Result<(), ApiError> {
    if std::env::var("MESHMIND_SEED_DEV_ADMIN").as_deref() != Ok("true") {
        return Ok(());
    }

    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    let hash = argon2
        .hash_password(b"admin", &salt)
        .map_err(|e| ApiError::Internal(anyhow::anyhow!("hash: {}", e)))?
        .to_string();

    let admin_role_id = Uuid::parse_str("00000000-0000-0000-0000-000000000001")
        .map_err(|_| ApiError::Internal(anyhow::anyhow!("invalid admin role id")))?;
    let default_workspace_id = Uuid::parse_str("00000000-0000-0000-0000-000000000002")
        .map_err(|_| ApiError::Internal(anyhow::anyhow!("invalid workspace id")))?;

    let user_id = sqlx::query_scalar::<_, Uuid>(
        r#"
        INSERT INTO users (username, password_hash, email, display_name)
        VALUES ('admin', $1, 'admin@localhost', 'Admin')
        ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash
        RETURNING id
        "#,
    )
    .bind(&hash)
    .fetch_one(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("seed admin: {}", e)))?;

    sqlx::query(
        r#"
        INSERT INTO user_roles (user_id, role_id)
        VALUES ($1, $2)
        ON CONFLICT (user_id, role_id) DO NOTHING
        "#,
    )
    .bind(user_id)
    .bind(admin_role_id)
    .execute(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("seed admin role: {}", e)))?;

    sqlx::query(
        r#"
        INSERT INTO workspace_users (workspace_id, user_id)
        VALUES ($1, $2)
        ON CONFLICT (workspace_id, user_id) DO NOTHING
        "#,
    )
    .bind(default_workspace_id)
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| ApiError::Internal(anyhow::anyhow!("seed admin workspace: {}", e)))?;

    tracing::info!(username = "admin", "seeded dev admin user");
    Ok(())
}
