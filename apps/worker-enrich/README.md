# MeshMind v2 — Enrichment Worker

Chunking and enrichment: token-aware chunking, language detection, classification, optional LLM enrichment.

## Running

```bash
pip install -e packages/meshmind-chunking -e apps/worker-runtime -e apps/worker-enrich

export CONTROL_API_URL=http://localhost:3000
export MESHMIND_AGENT_NAME=meshmind-enrich
export MESHMIND_AGENT_CAPABILITIES=enrich

python apps/worker-enrich/main.py
```

## Testing

```bash
pip install -e "apps/worker-enrich[dev]"
cd apps/worker-enrich && pytest -v
```
