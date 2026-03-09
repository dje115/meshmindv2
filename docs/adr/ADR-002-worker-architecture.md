# ADR-002: Worker Architecture

## Status

Accepted.

## Context

Ingestion involves heavy operations (PDF extraction, chunking, embeddings) that benefit from process isolation and language-specific libraries. v1 had connectors in-core (Rust); v2 separates extraction into external workers.

## Decision

- **Python workers:** Ingestion and embedding workers are implemented in Python.
- **Job-based model:** Core creates jobs; workers register, heartbeat, and claim jobs via HTTP.
- **No direct DB access:** Workers POST results to Core API; Core writes to storage.
- **Capabilities:** Workers declare capabilities (e.g. `ingest`, `embed`); Core assigns jobs accordingly.

## Consequences

- Python ecosystem for extraction (PyPDF2, python-docx, etc.) without Rust bindings.
- Workers can scale independently; multiple workers can run in parallel.
- Core retains control over job lifecycle and data integrity.
- Workers need network access to Core; API key or service token for auth.

## References

- INGESTION_PIPELINE.md
- SERVICE_BOUNDARIES.md
- DOMAIN_MODEL.md (Worker, IngestJob)
