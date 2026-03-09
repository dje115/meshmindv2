# ADR-003: Storage and Search

## Status

Accepted.

## Context

We need persistent storage for sources, jobs, artifacts, and search. v1 used CAS + Event Log + SQLite. v2 simplifies for server-first scope.

## Decision

- **SQLite:** Single SQLite database for all Core data.
- **FTS5:** Full-text search via SQLite FTS5 extension over artifact `body`.
- **Embeddings:** Store vector embeddings in SQLite (or separate vector store if needed later); hybrid search = FTS + cosine similarity.
- **Provenance:** Every artifact has `source_id` and metadata (file, page, table); no separate event log in v2 scope.

## Consequences

- Single file, easy backup and portability.
- FTS5 provides good keyword search; semantic search requires embedding storage.
- No CAS/event log in v2; schema is directly modeled (Sources, Jobs, Artifacts).
- If scale demands, we can migrate to Postgres or add a vector DB later.

## References

- DOMAIN_MODEL.md
- ARCHITECTURE.md
- INGESTION_PIPELINE.md
