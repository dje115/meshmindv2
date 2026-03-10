# MeshMind v2 — Documentation Index

> **Note:** MeshMind v1 ([github.com/dje115/meshmind](https://github.com/dje115/meshmind), `C:\Users\david\Documents\meshmind`) is **reference-only**. v2 is a clean-sheet redesign.

## Foundation Documents

| Document | Description |
|----------|-------------|
| [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md) | Purpose, capabilities, assumptions, non-goals |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Component overview, data flow, deployment |
| [DOMAIN_MODEL.md](DOMAIN_MODEL.md) | Core entities (Source, IngestJob, Artifact, Worker, etc.) |
| [SERVICE_BOUNDARIES.md](SERVICE_BOUNDARIES.md) | Core vs UI vs Worker responsibilities |
| [UI_SCREEN_LIST.md](UI_SCREEN_LIST.md) | Screens, routes, API dependencies |
| [INGESTION_PIPELINE.md](INGESTION_PIPELINE.md) | Source → Job → Worker → Core flow |
| [RBAC_MODEL.md](RBAC_MODEL.md) | Roles, permissions, API enforcement |
| [LOCAL_DEV_SETUP.md](LOCAL_DEV_SETUP.md) | Prerequisites, run/test commands, layout |

## Architecture Decision Records

| ADR | Title |
|-----|-------|
| [ADR-001-server-first.md](adr/ADR-001-server-first.md) | Server-first architecture |
| [ADR-002-worker-architecture.md](adr/ADR-002-worker-architecture.md) | Worker architecture (Python, job-based) |
| [ADR-003-storage-and-search.md](adr/ADR-003-storage-and-search.md) | Storage and search (SQLite, FTS5) |
| [ADR-004-local-model-runtime.md](adr/ADR-004-local-model-runtime.md) | Local model runtime (Ollama) |
| [ADR-005-server-first-worker-based.md](adr/ADR-005-server-first-worker-based.md) | Server-first and worker-based architecture |

## Environment & Setup

| Document | Description |
|----------|-------------|
| [DEVELOPER_PREREQUISITES.md](DEVELOPER_PREREQUISITES.md) | Install requirements, Developer PowerShell |
| [ENVIRONMENT_REPORT.md](ENVIRONMENT_REPORT.md) | Current environment status, verification |
| [OLLAMA_SETUP.md](OLLAMA_SETUP.md) | Ollama installation, detection, helper scripts |
| [MODEL_CONFIGURATION.md](MODEL_CONFIGURATION.md) | Pluggable model config, roles, profiles |
| [STARTUP_VALIDATION_DESIGN.md](STARTUP_VALIDATION_DESIGN.md) | Model availability validation at startup |
| [TEST_PLAN_MODEL_CONFIG.md](TEST_PLAN_MODEL_CONFIG.md) | Test coverage plan for config handling |
| [CONTROL_API_AUTH.md](CONTROL_API_AUTH.md) | Auth model (JWT, login) |
| [CONTROL_API_MIGRATIONS.md](CONTROL_API_MIGRATIONS.md) | Migration strategy |
| [CONTROL_API_CONVENTIONS.md](CONTROL_API_CONVENTIONS.md) | API conventions |
| [WORKER_PROTOCOL.md](WORKER_PROTOCOL.md) | Worker protocol (register, heartbeat, claim, complete, fail) |
| [FILESYSTEM_CONNECTOR.md](FILESYSTEM_CONNECTOR.md) | Filesystem connector: config, scan, provenance, reindex |
| [DOCUMENT_PROCESSING.md](DOCUMENT_PROCESSING.md) | Document processing worker: supported formats, Tika, tests |
| [OCR_AND_IMAGE_WORKERS.md](OCR_AND_IMAGE_WORKERS.md) | OCR and image workers: Tesseract, classification, provenance |
| [POST_EXTRACTION_PIPELINE.md](POST_EXTRACTION_PIPELINE.md) | Chunking, enrichment, embeddings flow |
| [CHUNKING_CONFIGURATION.md](CHUNKING_CONFIGURATION.md) | Chunk size, overlap, document types |
| [ENRICHMENT_SCHEMA.md](ENRICHMENT_SCHEMA.md) | Enrichment output schema |
| [EMBEDDING_VERSIONING.md](EMBEDDING_VERSIONING.md) | Model versioning, re-embed |
| [LOCAL_MODELS.md](LOCAL_MODELS.md) | Choosing local embedding models |
| [PROVENANCE_CHUNKING.md](PROVENANCE_CHUNKING.md) | Provenance through chunking/enrichment |
| [CONFIGURATION_AUDIT.md](CONFIGURATION_AUDIT.md) | Configuration audit: settings, env vars, migration plan |
