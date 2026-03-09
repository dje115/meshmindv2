# MeshMind v2 — RBAC Model

> **Note:** v1 had a policy engine. v2 uses a simpler RBAC model for v2 scope.

## Entities

| Entity | Description |
|--------|-------------|
| **User** | Identity (username, password hash or API key) |
| **Role** | Named set of permissions (e.g. `viewer`, `editor`, `admin`) |
| **Permission** | Action on resource (e.g. `sources:read`, `sources:write`, `admin:users`) |

## Relationships

- User has many Roles (N:M)
- Role has many Permissions (N:M)
- Effective permission = union of all permissions from user's roles

## Built-in roles

| Role | Permissions |
|------|-------------|
| **viewer** | `search:read`, `ask:read`, `sources:read`, `jobs:read` |
| **editor** | viewer + `sources:write`, `sources:ingest`, `jobs:read` |
| **admin** | editor + `admin:users`, `admin:roles`, `admin:workers` |

## Resource:action pattern

- `search:read` — Run search
- `ask:read` — Run Ask
- `sources:read` — List/view sources
- `sources:write` — Create/update/delete sources
- `sources:ingest` — Trigger ingest
- `jobs:read` — List jobs
- `admin:users` — Manage users
- `admin:roles` — Manage roles
- `admin:workers` — View workers

## API enforcement

- All API routes (except `/health`, `/auth/login`) require authentication
- Each route maps to a permission; Core checks before handling
- 401 if unauthenticated, 403 if insufficient permission

## Assumptions

- No per-artifact or per-source fine-grained ACLs in v2
- Worker uses service token with `sources:read`, `jobs:write`, `ingest:write`
- First user bootstrap: create admin user via migration or CLI
