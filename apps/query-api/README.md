# MeshMind v2 Query API

Python service for search and ask. Used by the control-api.

## Setup

```bash
cd apps/query-api
pip install -e .
# sentence-transformers + qdrant + asyncpg
```

## Run

```bash
QUERY_API_PORT=3001 python -m meshmind_query_api.main
# or
uvicorn meshmind_query_api.main:app --host 0.0.0.0 --port 3001
```

## Env

- `DATABASE_URL` - Postgres (for chunk_index FTS)
- `QDRANT_URL` - Qdrant (default http://localhost:6333)
- `OLLAMA_URL` - Ollama (for /ask)
- `MESHMIND_EMBED_MODEL` - Embedding model (same as worker-embed)
- `MESHMIND_ASK_MODEL` - LLM model (default llama3.2)
