# MeshMind v2 — Embeddings Worker

Generates vectors for chunks and stores them in Qdrant.

## Requirements

- Qdrant server (http://localhost:6333)
- sentence-transformers: `pip install 'meshmind-worker-embed[sentence-transformers]'`

## Running

```bash
pip install -e apps/worker-runtime -e apps/worker-embed
pip install 'meshmind-worker-embed[sentence-transformers]'

export CONTROL_API_URL=http://localhost:3000
export MESHMIND_AGENT_NAME=meshmind-embed
export MESHMIND_AGENT_CAPABILITIES=embed
export QDRANT_URL=http://localhost:6333
export MESHMIND_EMBED_MODEL=all-MiniLM-L6-v2

python apps/worker-embed/main.py
```
