//! Entity types matching database schema.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub username: String,
    #[serde(skip_serializing)]
    pub password_hash: Option<String>,
    pub email: Option<String>,
    pub display_name: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Role {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Workspace {
    pub id: Uuid,
    pub name: String,
    pub slug: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "source_kind", rename_all = "snake_case")]
pub enum SourceKind {
    Filesystem,
    Sqlite,
    Csv,
    Json,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "source_status", rename_all = "snake_case")]
pub enum SourceStatus {
    Pending,
    Approved,
    Ingesting,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow, utoipa::ToSchema)]
pub struct SourceItem {
    pub id: Uuid,
    pub source_id: Uuid,
    pub fingerprint: String,
    pub provenance: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Source {
    pub id: Uuid,
    pub workspace_id: Uuid,
    pub name: String,
    pub kind: SourceKind,
    pub config: serde_json::Value,
    pub status: SourceStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "agent_status", rename_all = "snake_case")]
pub enum AgentStatus {
    Active,
    Stale,
    Dead,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Agent {
    pub id: Uuid,
    pub name: String,
    pub capabilities: Vec<String>,
    pub status: AgentStatus,
    pub last_heartbeat: DateTime<Utc>,
    #[serde(skip_serializing)]
    pub agent_token: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Worker capability enum (filesystem, email, ocr, image, embed, docproc, enrich)
#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type, PartialEq, Eq, Hash, utoipa::ToSchema)]
#[sqlx(type_name = "worker_capability", rename_all = "snake_case")]
pub enum WorkerCapability {
    Filesystem,
    Email,
    Ocr,
    Image,
    Embed,
    Docproc,
    Enrich,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AgentCapability {
    pub id: Uuid,
    pub agent_id: Uuid,
    pub capability: WorkerCapability,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AgentAssignment {
    pub id: Uuid,
    pub source_id: Uuid,
    pub agent_id: Uuid,
    pub assigned_at: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "job_run_status", rename_all = "snake_case")]
pub enum JobRunStatus {
    Running,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct JobRun {
    pub id: Uuid,
    pub job_id: Uuid,
    pub agent_id: Uuid,
    pub status: JobRunStatus,
    pub started_at: DateTime<Utc>,
    pub ended_at: Option<DateTime<Utc>>,
    pub error: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "job_log_level", rename_all = "snake_case")]
pub enum JobLogLevel {
    Info,
    Warn,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct JobLog {
    pub id: Uuid,
    pub job_id: Uuid,
    pub job_run_id: Option<Uuid>,
    pub agent_id: Option<Uuid>,
    pub level: JobLogLevel,
    pub message: String,
    pub details: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type, PartialEq, Eq, utoipa::ToSchema)]
#[sqlx(type_name = "job_status", rename_all = "snake_case")]
pub enum JobStatus {
    Queued,
    Claimed,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow, utoipa::ToSchema)]
pub struct Job {
    pub id: Uuid,
    pub source_id: Uuid,
    pub source_item_id: Option<Uuid>,
    pub agent_id: Option<Uuid>,
    pub job_kind: Option<WorkerCapability>,
    pub status: JobStatus,
    pub claimed_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error: Option<String>,
    pub retry_count: i32,
    pub max_retries: i32,
    pub next_retry_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AuditEvent {
    pub id: Uuid,
    pub workspace_id: Option<Uuid>,
    pub user_id: Option<Uuid>,
    pub action: String,
    pub resource_type: String,
    pub resource_id: Option<Uuid>,
    pub request_id: Option<String>,
    pub details: serde_json::Value,
    pub created_at: DateTime<Utc>,
}
