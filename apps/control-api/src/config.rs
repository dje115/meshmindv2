//! Configuration for control-api.
//!
//! Loads from env and optional TOML. Compatible with shared infra config.

use serde::Deserialize;
use std::path::PathBuf;

/// Control API configuration.
#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct Config {
    pub http_bind: String,
    pub data_dir: PathBuf,
    pub database_url: String,
    pub redis_url: String,
    pub ollama_url: String,
    pub cors_enabled: bool,
    pub jwt_secret: String,
    pub seed_dev_admin: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            http_bind: std::env::var("CONTROL_API_PORT")
                .map(|p| format!("0.0.0.0:{}", p))
                .unwrap_or_else(|_| "0.0.0.0:3000".to_string()),
            data_dir: PathBuf::from("./data"),
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgres://meshmind:meshmind@localhost:5432/meshmind".to_string()),
            redis_url: std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://localhost:6379".to_string()),
            ollama_url: std::env::var("OLLAMA_URL")
                .unwrap_or_else(|_| "http://localhost:11434".to_string()),
            cors_enabled: true,
            jwt_secret: "change-me-in-production".to_string(),
            seed_dev_admin: false,
        }
    }
}

impl Config {
    /// Load config from TOML file, merging with env.
    pub fn from_file(path: &std::path::Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let mut config: Config = toml::from_str(&content)?;
        Self::apply_env(&mut config);
        Ok(config)
    }

    /// Load config from env or default path.
    pub fn load() -> anyhow::Result<Self> {
        let path = std::env::var("MESHMIND_CONFIG")
            .unwrap_or_else(|_| "meshmind.toml".to_string());
        let p = std::path::Path::new(&path);
        if p.exists() {
            Self::from_file(p)
        } else {
            let mut config = Config::default();
            Self::apply_env(&mut config);
            Ok(config)
        }
    }

    fn apply_env(config: &mut Config) {
        if let Ok(v) = std::env::var("CONTROL_API_PORT") {
            config.http_bind = format!("0.0.0.0:{}", v);
        }
        if let Ok(v) = std::env::var("DATABASE_URL") {
            config.database_url = v;
        }
        if let Ok(v) = std::env::var("REDIS_URL") {
            config.redis_url = v;
        }
        if let Ok(v) = std::env::var("OLLAMA_URL") {
            config.ollama_url = v;
        }
        if let Ok(v) = std::env::var("JWT_SECRET") {
            config.jwt_secret = v;
        }
        if let Ok(v) = std::env::var("MESHMIND_SEED_DEV_ADMIN") {
            config.seed_dev_admin = v == "true" || v == "1";
        }
    }
}
