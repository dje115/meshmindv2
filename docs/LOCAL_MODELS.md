# MeshMind v2 — Choosing Local Models

## Embedding Models

| Provider | Model | Dimension | Install |
|----------|-------|-----------|---------|
| sentence-transformers | all-MiniLM-L6-v2 | 384 | `pip install sentence-transformers` |
| sentence-transformers | all-mpnet-base-v2 | 768 | Same |

## Enrichment

- **Deterministic**: langdetect (no model)
- **Optional LLM**: Implement `EnrichmentProvider` and wire to Ollama or local API

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| MESHMIND_EMBED_MODEL | all-MiniLM-L6-v2 | Embedding model name |
| QDRANT_URL | http://localhost:6333 | Qdrant server |
