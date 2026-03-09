# MeshMind v2 — Architecture

> **Note:** v1 is reference-only. v2 is a clean-sheet architecture.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (React UI)                           │
│         Ask │ Search │ Sources │ Jobs │ Admin                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MeshMind Core (Rust)                            │
│   Axum HTTP API │ Job Queue │ RBAC │ Storage │ Search            │
└─────────────────────────────────────────────────────────────────┘
         │                    │                      │
         ▼                    ▼                      ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   SQLite     │    │  Python Workers  │    │     Ollama       │
│  (data +     │    │  (ingest, embed) │    │  (inference)     │
│   FTS)       │    │  register/heart- │    │                  │
│              │    │  beat, claim jobs│    │                  │
└──────────────┘    └──────────────────┘    └──────────────────┘
```

## Components

| Component | Tech | Role |
|-----------|------|------|
| Core | Rust (Axum) | HTTP API, job coordination, storage, search, RBAC |
| UI | React | Browser-based interface |
| Workers | Python | Document extraction, chunking, embedding; claim jobs from core |
| Storage | SQLite | Artifacts, chunks, embeddings, job state, user/role data |
| Inference | Ollama | Local LLM for Ask and embeddings |

## Data flow

1. **Ingestion:** User registers source → Core creates ingest job → Worker claims job → Worker extracts, chunks → Worker posts results to Core → Core stores with provenance
2. **Search:** User queries → Core hybrid search (FTS + semantic) → Returns ranked chunks with provenance
3. **Ask:** User question → Core retrieves relevant chunks → Core calls Ollama → Returns answer with citations

## Deployment

- Docker Compose: `core`, `ui`, `worker` (or multiple workers), `ollama` (or host Ollama)
- Core is the single source of truth; workers are stateless job executors
