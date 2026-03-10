# MeshMind v2 — Embedding Versioning

## Collection Naming

Collections are versioned by model: `meshmind_{model_safe}`.

Example: `meshmind_all-MiniLM-L6-v2` for sentence-transformers default.

## Re-embed Jobs

- Changing `MESHMIND_EMBED_MODEL` creates a new collection
- Old vectors remain; new ingestion uses the new model
- Re-embed: re-run the pipeline for a source to populate a new collection

## Model Selection

| Model | Dimension | Notes |
|-------|-----------|-------|
| all-MiniLM-L6-v2 | 384 | Default, fast, good quality |
| all-mpnet-base-v2 | 768 | Higher quality, slower |

Set via `MESHMIND_EMBED_MODEL` env var.
