# MeshMind v2 — Domain Model

> **Note:** v1 is reference-only. v2 domain model is simplified for server-first architecture.

## Core entities

### Workspace

Tenant/scope for sources and users.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Display name |
| slug | string | Unique slug |
| description | string? | |
| created_at, updated_at | timestamp | |

### User

Identity with password hash and optional email/display_name.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| username | string | Unique |
| password_hash | string | Argon2 |
| email | string? | |
| display_name | string? | |
| created_at, updated_at | timestamp | |

### Role, Permission

RBAC entities (see RBAC_MODEL.md). User has many Roles; Role has many Permissions.

### Source

A registered data source (file path, DB connection string, folder) that can be ingested.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| workspace_id | UUID | FK to Workspace |
| name | string | |
| kind | enum | filesystem, sqlite, csv, json |
| config | JSON | Path, connection, filters |
| status | enum | pending, approved, ingesting, completed, failed |
| created_at, updated_at | timestamp | |

### Agent

Registered worker process that can claim jobs.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | |
| capabilities | string[] | e.g. ["ingest", "embed"] |
| status | enum | active, stale, dead |
| last_heartbeat | timestamp | |
| created_at, updated_at | timestamp | |

### Job

A unit of work for ingestion, claimed by an agent.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| source_id | UUID | FK to Source |
| agent_id | UUID? | FK to Agent if claimed |
| status | enum | queued, claimed, completed, failed |
| claimed_at | timestamp? | |
| completed_at | timestamp? | |
| error | text? | If failed |
| created_at, updated_at | timestamp | |

### AuditEvent

Audit log entry for actions.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| workspace_id | UUID? | FK to Workspace |
| user_id | UUID? | FK to User |
| action | string | e.g. "workspace.create" |
| resource_type | string | e.g. "workspace" |
| resource_id | UUID? | |
| request_id | string? | Correlation ID |
| details | JSON | |
| created_at | timestamp | |

## Relationships

- Workspace → Source (1:N)
- Workspace → WorkspaceUser (1:N)
- User → Role (N:M)
- Role → Permission (N:M)
- Source → Job (1:N)
- Job → Agent (N:1, when claimed)
