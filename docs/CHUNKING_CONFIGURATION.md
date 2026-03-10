# MeshMind v2 — Chunking Configuration

## Overview

Chunking splits documents into fixed-size segments while preserving page and sheet references. It uses sentence-boundary-aware splitting when possible.

## Configuration

### ChunkConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| defaults | DocumentTypeConfig | PDF defaults | Fallback when document type unknown |
| by_document_type | dict | See below | Per-type overrides |

### DocumentTypeConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| chunk_size | int | 600 | Target chars per chunk (~tokens/4) |
| overlap | int | 100 | Overlap between chunks |
| min_chunk_chars | int | 50 | Minimum chunk length |
| prefer_sentence_boundaries | bool | True | Prefer splitting at sentence ends |

### Defaults by Document Type

| Type | chunk_size | overlap |
|------|------------|---------|
| pdf | 600 | 100 |
| docx | 600 | 100 |
| spreadsheet | 800 | 120 |
| image, ocr | 500 | 80 |
| plain | 600 | 100 |

## Token-Aware Behavior

- Approximate tokens ≈ `chars / 4` for English
- Splitting prefers sentence boundaries (`.`, `!`, `?` + space)
- Fallback: sliding window with overlap
