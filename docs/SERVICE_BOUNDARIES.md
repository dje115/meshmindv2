# MeshMind v2 — Service Boundaries

> **Note:** v1 is reference-only. v2 has clear service boundaries.

## Services

| Service | Repo/crate | Responsibilities |
|---------|------------|------------------|
| **Core** | `crates/core` (Rust) | HTTP API, job queue, storage, search, RBAC, worker registration |
| **UI** | `ui/` (React) | SPA for Ask, Search, Sources, Jobs, Admin |
| **Worker** | `worker/` (Python) | Claim ingest/embed jobs, extract content, POST results to Core |
| **Ollama** | External | LLM inference; Core calls via HTTP |

## Boundaries

### Core owns

- All persistent state (SQLite)
- Job lifecycle (create, assign, complete, fail)
- Worker registration and heartbeat
- Authentication and authorization
- Search index
- Provenance metadata

### Worker does not own

- No database; all writes go through Core API
- No user/auth; uses API key or service token from Core
- No direct Ollama calls for Ask (Core does that); workers may call Ollama for embeddings if delegated

### UI does not own

- No direct DB access
- All actions via Core HTTP API
- Session/token from Core auth

## Communication

| From | To | Protocol |
|------|-----|----------|
| UI | Core | HTTP/REST |
| Worker | Core | HTTP/REST (register, heartbeat, claim job, POST results) |
| Core | Ollama | HTTP (generate, embed) |

## Data flow across boundaries

1. **Ingestion:** UI → Core (create source, trigger ingest) → Core creates job → Worker polls/claims → Worker POSTs chunks → Core stores
2. **Search:** UI → Core (search) → Core queries DB → UI displays
3. **Ask:** UI → Core (ask) → Core retrieves chunks → Core → Ollama → Core returns answer → UI displays
