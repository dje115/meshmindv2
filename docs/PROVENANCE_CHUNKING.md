# MeshMind v2 — Provenance Through Chunking and Enrichment

## Chain

```
source_item (provenance) → document → chunks → Qdrant points
```

## Preserved Fields

| Stage | Fields |
|-------|--------|
| Chunk metadata | page_index, sheet_index, sheet_name, provenance, absolute_path, open_target, filename |
| Qdrant payload | source_item_id, source_id, chunk_id, text, metadata (incl. provenance) |

## Citation Flow

1. Search returns chunk_id, source_item_id, page_index, absolute_path
2. UI can show "Page 3 of report.pdf"
3. "Open original" uses open_target (file:// URL)

## Low-Confidence OCR

Chunks from low-confidence OCR pages carry `low_confidence: true` in metadata for UI badges or filtering.
