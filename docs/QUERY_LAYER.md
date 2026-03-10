# MeshMind v2 — Query Layer

## Overview

The query layer provides search, document detail, provenance, and grounded chat (ask) with citations. All endpoints enforce workspace-scoped permissions before retrieval.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | GET | Hybrid search (keyword + vector) |
| `/api/documents/:id` | GET | Document detail with chunks |
| `/api/documents/:id/provenance` | GET | Provenance metadata |
| `/api/ask` | POST | Grounded chat answer with citations |

## Hybrid Retrieval

Search uses **true hybrid retrieval**, not vector-only:

1. **Keyword search**: Postgres full-text search (FTS) on the `chunk_index` table via `tsvector`/`plainto_tsquery`.
2. **Vector search**: Qdrant similarity search on the collection `meshmind_{model}` (e.g. `meshmind_all-MiniLM-L6-v2`).
3. **Merge**: Reciprocal Rank Fusion (RRF) with k=60. Results from both paths are merged by `(chunk_id, source_item_id)`. A chunk that appears in both keyword and vector results gets a higher RRF score (hybrid match).

Keyword search requires the `chunk_index` table to be populated. The embed worker calls `/api/workers/source-items/:id/index-chunks` after embedding, so chunks are indexed automatically when documents are embedded.

## Ranking Approach

- **Keyword**: `ts_rank(search_vector, plainto_tsquery('english', q))` for FTS relevance.
- **Vector**: Qdrant cosine similarity score.
- **RRF**: `sum(1 / (k + rank))` for each ranking list, k=60.

## Citation Format

- Citations are inline in the answer as `[chunk_id]` (e.g. `[chunk_item1_0_abc123]`).
- The `/ask` response includes a `citations` array with: `chunk_id`, `source_item_id`, `text`, `page_index`, `sheet_index`, `sheet_name`, `score`.

## Provenance

- `GET /api/documents/:id/provenance` returns: `source_item_id`, `source_id`, `workspace_id`, `provenance` JSON, `absolute_path`, `filename`, `open_target`.
- Page/sheet metadata (e.g. "Page 3 of report.pdf") comes from chunk payloads or provenance.

## What Makes an Answer Grounded

An answer is **grounded** when:

1. It is derived from retrieved chunks only.
2. Every factual claim is cited with a chunk ID.
3. The LLM is instructed not to invent facts and to say when context is insufficient.
4. The response model includes `grounded: true/false`, `citations`, `confidence`, `coverage`.

## Local vs External Research

- **Local** (`source_type: "local"`): Answer from workspace documents. The current implementation is local-only.
- **External** (future): Web/internet research. The response model distinguishes `source_type: "local"` from `"external"` so the UI can show provenance clearly.

## Limitations of Grounded Answers

- Groundedness depends on LLM compliance; strict citation enforcement is best-effort.
- If Ollama is unavailable, a fallback message is returned with available chunks.
- Empty search results produce a "no relevant content" message rather than a fabricated answer.
- Confidence/coverage are heuristic (e.g. citation count / chunk count).

## Architecture

- **Control API (Rust)**: Auth, permission checks (`search:read`, `ask:read`), workspace resolution, proxy to query-api for search/ask.
- **Query API (Python)**: Hybrid search, ask (Ollama), uses Postgres (`chunk_index`) and Qdrant.
- **Embed Worker**: Writes vectors to Qdrant and chunks to `chunk_index` via the index-chunks endpoint.

## Configuration

- `QUERY_API_URL`: Control-API → Query-API base URL (default: `http://localhost:3001`).
- Query-API: `DATABASE_URL`, `QDRANT_URL`, `OLLAMA_URL`, `MESHMIND_EMBED_MODEL`, `MESHMIND_ASK_MODEL`.
