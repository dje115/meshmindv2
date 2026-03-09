# MeshMind v2 — Product Scope

> **Note:** MeshMind v1 (see [github.com/dje115/meshmind](https://github.com/dje115/meshmind) and `C:\Users\david\Documents\meshmind`) is **reference-only**. v2 is a clean-sheet redesign with different architecture and scope.

## Purpose

MeshMind v2 is an **on-prem, server-first, browser-first AI knowledge platform**. It ingests documents and structured data, indexes them for search, and answers questions using local LLMs (Ollama). Data stays on your infrastructure.

## Core Capabilities (in scope)

| Capability | Description |
|------------|-------------|
| Document ingestion | PDF, DOCX, TXT, MD via Python workers; chunking, extraction, storage |
| Structured data ingestion | SQLite, CSV, JSON via workers |
| Hybrid search | Full-text + semantic search over ingested content |
| Provenance | Track source of every chunk and artifact |
| Q&A / Ask | Answer questions over indexed content with citations |
| RBAC | Role-based access control for users and API |
| Worker job model | Workers register, heartbeat, claim jobs from core |
| Docker-first | Core + workers + UI via Docker Compose |

## Assumptions

- Single-tenant or controlled multi-tenant deployments
- Local LLM inference via Ollama (no cloud LLM in v2)
- No peer-to-peer mesh; single server or conventional load balancer
- Browser-based UI; no desktop app
- Python for ingestion workers (extraction libraries, simpler integration)
- Rust for core (API, storage, job coordination)

## Non-goals (out of v2 scope)

| Non-goal | Rationale |
|----------|-----------|
| Peer-to-peer mesh | v2 is server-centric |
| Federated learning | Not in initial scope |
| On-device training / custom model training | Future phase |
| Web research / external crawl | Not in v2 core |
| Mobile apps | Browser-first |
| Real-time collaboration | Not required for v2 |
| Offline-first / local-first sync | Server is source of truth |

## Success criteria

- User can ingest documents and query them via UI
- Search returns relevant chunks with provenance
- Ask produces answers with citations
- RBAC enforces permissions on API and UI
- Docker Compose runs the full stack
