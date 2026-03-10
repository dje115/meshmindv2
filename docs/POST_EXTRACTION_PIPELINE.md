# MeshMind v2 — Post-Extraction Pipeline

## Overview

After extraction (docproc, OCR, image workers), the pipeline runs:

1. **Chunking** — Token-aware splitting with page/sheet refs
2. **Enrichment** — Language detection, classification, optional LLM enrichment
3. **Embeddings** — Vector generation and storage in Qdrant

## Flow

```
docproc/ocr/image complete → enrich job → chunk + enrich → embed job → vectors in Qdrant
```

- **Docproc/OCR/Image** workers create `enrich` jobs on completion
- **Enrich worker** fetches document artifacts, chunks, enriches, creates `embed` jobs
- **Embed worker** fetches chunks, generates vectors, stores in Qdrant (deterministic point IDs from chunk_id/source_item_id+chunk_index for stable re-embedding)

## Components

| Component | Package | Capability |
|-----------|---------|------------|
| Chunking | packages/meshmind-chunking | Library |
| Enrichment worker | apps/worker-enrich | enrich |
| Embeddings worker | apps/worker-enrich | embed |

## Provenance and Source Location

Provenance is preserved through all stages:

- **Chunk metadata**: `page_index`, `sheet_index`, `sheet_name`, `provenance`, `absolute_path`, `open_target`, `filename`
- **Qdrant payload**: Each point stores `source_item_id`, `source_id`, chunk metadata, and `text` for hybrid search

This supports "open original file" and citation flows in search/chat.
