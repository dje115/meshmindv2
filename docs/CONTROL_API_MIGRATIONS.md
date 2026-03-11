# MeshMind v2 — Migration Strategy

## Overview

Migrations live in `apps/control-api/migrations/` and are run automatically on startup via `sqlx::migrate!()`.

## Migration Files

| File | Description |
|------|-------------|
| 001_create_roles.sql | Roles and permissions |
| 002_create_workspaces.sql | Workspaces |
| 003_create_users.sql | Users, user_roles, workspace_users |
| 004_create_sources.sql | Sources |
| 005_create_agents.sql | Agents (workers) |
| 006_create_jobs.sql | Jobs |
| 007_create_audit_events.sql | Audit events |
| 008_seed_dev_admin.sql | Seed permissions, admin role, default workspace |
| 009_worker_protocol.sql | agent_capabilities, agent_assignments, job_runs, job_logs, retry columns |
| 010_source_items.sql | source_items table |
| 011_add_job_kind.sql | job_kind column on jobs |
| 012_add_enrich_capability.sql | enrich in worker_capability enum |
| 013_chunk_index.sql | chunk_index table |
| 014_app_settings.sql | app_settings table, settings:read/write |

## Running Migrations

- **Automatic:** Migrations run on control-api startup (`db::migrate(&pool).await`)
- **Manual:** `sqlx migrate run` from `apps/control-api` (requires `sqlx-cli`)

## Dev Admin User

Migration 008 seeds roles and default workspace. The **admin user** is created by application code when `MESHMIND_SEED_DEV_ADMIN=true`.

## SQLx Offline Mode

For CI without a database, use `SQLX_OFFLINE=true` and run `sqlx prepare` once with a live DB to generate `.sqlx/` cache.
