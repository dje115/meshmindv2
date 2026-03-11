# MeshMind v2 — Worker Protocol

## Overview

Workers (agents) register with the control plane, fetch config, claim jobs, heartbeat, and report progress/errors. Workers are stateless; the control plane owns schedules, job creation, retries, and backoff.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/workers/register` | Register a new agent |
| POST | `/api/workers/heartbeat` | Record heartbeat |
| POST | `/api/workers/jobs/claim` | Claim a queued job |
| POST | `/api/workers/jobs/:id/progress` | Report progress |
| POST | `/api/workers/jobs/:id/complete` | Mark job completed |
| POST | `/api/workers/jobs/:id/fail` | Mark job failed (control plane handles retry) |

## Data Model

- **agents** — Worker identity, capabilities, status, last_heartbeat
- **agent_capabilities** — Normalized capability model (filesystem, email, ocr, image, embed, docproc)
- **agent_assignments** — Source-to-worker assignment (optional preference)
- **job_runs** — Per-attempt tracking for retries
- **job_logs** — Progress and error logs

## API Examples

### Register

Capabilities must use **snake_case** (e.g. `filesystem`, `docproc`, not `Filesystem`).

```bash
curl -X POST http://localhost:3000/api/workers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fs-worker-1",
    "capabilities": ["filesystem", "docproc"]
  }'
```

Response:
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "token": "wk_abc123...",
  "config_url": "/api/workers/config"
}
```

> **TODO (Phase 3+):** Hash agent tokens before storage (e.g. Argon2) when token-based worker auth is enforced. Currently tokens are stored plain text and worker endpoints identify by `agent_id` only.

### Heartbeat

```bash
curl -X POST http://localhost:3000/api/workers/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

Response:
```json
{
  "status": "active",
  "last_heartbeat": "2025-03-09T12:00:00Z"
}
```

### Claim Job

```bash
curl -X POST http://localhost:3000/api/workers/jobs/claim \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "capabilities": ["filesystem"]
  }'
```

Response (200 with job):
```json
{
  "job_id": "...",
  "job_run_id": "...",
  "source_id": "...",
  "source": { "id": "...", "name": "docs", "kind": "filesystem", "config": {} },
  "config": { "path": "/data/docs", "extensions": ["pdf", "txt"] }
}
```

Response (204): No job available.

### Progress

```bash
curl -X POST http://localhost:3000/api/workers/jobs/{job_id}/progress \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_run_id": "...",
    "message": "Extracted 10 chunks",
    "details": { "chunks": 10 }
  }'
```

### Complete

```bash
curl -X POST http://localhost:3000/api/workers/jobs/:job_id/complete \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_run_id": "...",
    "artifacts": []
  }'
```

### Fail

```bash
curl -X POST http://localhost:3000/api/workers/jobs/:job_id/fail \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_run_id": "...",
    "error": "File not found: /path/to/doc.pdf"
  }'
```

## Sequence Diagrams

### Register / Heartbeat

```mermaid
sequenceDiagram
    participant W as Worker
    participant C as Control Plane

    W->>C: POST /workers/register { name, capabilities }
    C->>C: Create agent, agent_capabilities
    C->>W: 200 { agent_id, token }

    loop Every 30-60s
        W->>C: POST /workers/heartbeat { agent_id }
        C->>C: Update last_heartbeat, status=active
        C->>W: 200 { status, last_heartbeat }
    end
```

### Claim / Complete

```mermaid
sequenceDiagram
    participant W as Worker
    participant C as Control Plane

    W->>C: POST /workers/jobs/claim { agent_id, capabilities }
    C->>C: SELECT job FOR UPDATE SKIP LOCKED
    alt Job available
        C->>C: Update job (claimed), create job_run
        C->>W: 200 { job_id, job_run_id, source, config }
        W->>W: Process job
        W->>C: POST /workers/jobs/{id}/progress { message, details }
        W->>C: POST /workers/jobs/{id}/complete { artifacts }
        C->>C: Update job (completed), job_run
        C->>W: 200
    else No job
        C->>W: 204 No Content
    end
```

### Failure / Retry

```mermaid
sequenceDiagram
    participant W as Worker
    participant C as Control Plane

    W->>C: POST /workers/jobs/claim
    C->>W: 200 { job_id, job_run_id, ... }

    W->>W: Process job (fails)
    W->>C: POST /workers/jobs/{id}/fail { error }
    C->>C: Update job_run (failed), job (retry_count++)
    C->>C: If retries < max: status=queued, next_retry_at
    C->>C: If retries >= max: status=failed
    C->>W: 200

    Note over C: Control plane schedules retry at next_retry_at
    W->>C: POST /workers/jobs/claim (later)
    C->>W: 200 (same job, re-queued)
```

## Worker Capabilities

| Capability | Description |
|------------|-------------|
| filesystem | Local/remote filesystem access |
| email | Email inbox ingestion |
| ocr | OCR for images/PDFs |
| image | Image processing |
| embed | Embedding generation |
| docproc | Document processing (PDF, DOCX, etc.) |

Source kind maps to required capability:
- `filesystem` → filesystem
- `sqlite`, `csv`, `json` → docproc

## Agent Status (Stale/Dead)

A background task runs every 60 seconds when the control plane starts. It updates agent status based on `last_heartbeat`:

| Threshold | Status  | Description                          |
|-----------|---------|--------------------------------------|
| &lt; 90s  | active  | Agent has heartbeated recently       |
| ≥ 90s     | stale   | No heartbeat for 90+ seconds         |
| ≥ 300s    | dead    | No heartbeat for 300+ seconds        |

Only agents with `status = active` can claim jobs.

## Rules

- **Workers are stateless** where possible; no local job queue.
- **Control plane owns** schedules, job creation, retries, backoff.
- **Workers never mutate** business config directly.
- **Retries and backoff** are controlled centrally (retry_count, max_retries, next_retry_at).

## Worker Lifecycle Summary

1. **Register** — Worker calls `POST /workers/register` with name and capabilities. Control plane creates agent record and agent_capabilities. Returns `agent_id` and `token`.
2. **Heartbeat** — Worker polls `POST /workers/heartbeat` every 30–60s with `agent_id`. Control plane updates `last_heartbeat` and sets `status=active`. A background task in the control plane runs every 60s and marks agents stale (no heartbeat >90s) or dead (>300s).
3. **Claim** — Worker polls `POST /workers/jobs/claim` with `agent_id` and `capabilities`. Control plane atomically selects a queued job (capability match, assignment preference), locks it, creates job_run, returns job payload. 204 if no job.
4. **Process** — Worker does the work; optionally reports progress via `POST /workers/jobs/{id}/progress`.
5. **Complete or Fail** — Worker calls `POST /workers/jobs/{id}/complete` or `POST /workers/jobs/{id}/fail`. On fail, control plane increments retry_count, sets next_retry_at (exponential backoff), and re-queues the job until max_retries.
6. **Claim again** — Worker loops to step 3.

## Resetting Stuck Jobs

If a worker crashes after claiming a job but before completing or failing it, the job remains in `claimed` status and blocks re-processing. Use one of:

**API (authenticated):**
```bash
curl -X POST http://localhost:3000/api/jobs/reset-stuck \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
# Response: { "reset": 1 }
```

**Script:**
```bash
python scripts/reset_stuck_jobs.py
```

Requires `DATABASE_URL` (default: `postgres://meshmind:meshmind@localhost:5432/meshmind`).

## Adding a New Worker Type

To add a new worker capability (e.g. `slack`):

1. **Migration** — Add the capability to `worker_capability` enum in a new migration:
   ```sql
   ALTER TYPE worker_capability ADD VALUE 'slack';
   ```
2. **Entity** — Add variant to `WorkerCapability` in `entities.rs`:
   ```rust
   pub enum WorkerCapability {
       ...
       Slack,
   }
   ```
3. **Source mapping** (optional) — If a source kind requires this capability, update the claim SQL in `services/workers.rs` (CASE for `source.kind` → capability).
4. **Worker implementation** — Implement a worker that registers with `capabilities: ["slack"]`, claims jobs, and completes or fails. No control-plane code changes needed beyond (1)–(3).
