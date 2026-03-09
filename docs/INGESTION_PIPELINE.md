# MeshMind v2 — Ingestion Pipeline

> **Note:** v1 had in-core connectors. v2 uses Python workers that claim jobs from Core.

## Overview

```
User adds source (Core) → Core creates IngestJob → Worker claims job
  → Worker extracts/chunks → Worker POSTs chunks to Core
  → Core stores Artifacts with provenance
```

## Stages

### 1. Source registration (Core)

- User adds source via UI or API: `POST /api/sources`
- Payload: `{ kind, config }` (e.g. `kind: "filesystem"`, `config: { path, extensions }`)
- Core creates Source record, status `pending` or `approved`

### 2. Ingest trigger (Core)

- User triggers ingest: `POST /api/sources/:id/ingest`
- Core creates IngestJob(s) for the source, status `queued`

### 3. Job claim (Worker → Core)

- Worker polls: `POST /api/workers/jobs/claim` with `{ capabilities: ["ingest"] }`
- Core assigns a queued job, sets `claimed_by`, `claimed_at`
- Returns job payload: `{ job_id, source_id, source_config, ... }`

### 4. Extraction (Worker)

- Worker reads source (files, DB, etc.)
- Extracts text (PDF, DOCX, etc.), chunks (e.g. 1500 chars, 200 overlap)
- Optionally generates embeddings (or Core does post-ingest)
- Produces `Artifact[]` with provenance metadata

### 5. Result submission (Worker → Core)

- Worker POSTs: `POST /api/ingest/jobs/:id/complete` with `{ artifacts: [...] }`
- Core stores Artifacts, links to source, sets job `completed`
- On error: `POST /api/ingest/jobs/:id/fail` with `{ error }`

## Artifact schema (Worker → Core)

```json
{
  "content_hash": "sha256:...",
  "content_type": "chunk",
  "body": "extracted text...",
  "metadata": {
    "source_file": "doc.pdf",
    "page": 1,
    "chunk_index": 0
  },
  "embedding": [0.1, -0.2, ...]  // optional
}
```

## Worker responsibilities

- Support source kinds: `filesystem`, `sqlite`, `csv`, `json`
- Chunking: configurable size/overlap
- Provenance: include `source_file`, `page`, `table`, etc. in metadata
- Retries: Worker may retry failed extractions; Core records final status

## Core responsibilities

- Job lifecycle, claim semantics (one worker per job)
- Store artifacts, maintain provenance
- Reject invalid payloads, idempotency where applicable
