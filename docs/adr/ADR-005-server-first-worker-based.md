# ADR-005: Server-First and Worker-Based Architecture

## Status

Accepted.

## Context

MeshMind v1 was local-first with peer-to-peer mesh. v2 targets on-prem deployments where a central control plane orchestrates all work. Specialized ingestion (document extraction, OCR, images) benefits from process isolation and language-specific libraries.

## Decision

### Server-first

- **Control API (Rust)** is the main control plane. It owns:
  - Sources, jobs, agents, permissions
  - Search (Qdrant, Meilisearch)
  - Chat (Ollama)
  - Worker registration and job assignment

- **All ingestion happens outside the core.** Workers perform extraction and POST results to the control API. The core never reads files directly.

- **No cloud dependency.** Postgres, Redis, Qdrant, Meilisearch, Ollama run locally or on-prem.

### Worker-based

- **Workers are specialized processes** (Python for docproc, OCR, image; possibly Rust for embed).
- Workers register with the control API, heartbeat, and claim jobs.
- Workers are stateless; they receive job payloads, do work, POST results.
- **worker-connectors** provides connector logic (filesystem first); workers use it to read sources and produce normalized output.

### Modular boundaries

- **apps/control-api** — Rust, single binary
- **apps/web** — React SPA, consumes control API
- **apps/worker-*** — One app per worker type; shared runtime in worker-runtime
- **packages/contracts** — OpenAPI + JSON Schemas for inter-service contracts

## Consequences

- Simpler deployment: one control API, scale workers independently.
- Clear responsibility: control API orchestrates; workers execute.
- Independently testable: each service has its own tests.
- Docker Compose provides a full local dev environment.

## References

- PRODUCT_SCOPE.md
- ARCHITECTURE.md
- SERVICE_BOUNDARIES.md
