# MeshMind v2 — Startup Validation Design

This document describes the design for Ollama and model availability validation at Core startup.

## Goals

1. **Fail fast:** If critical models are missing, report clearly before accepting requests.
2. **Actionable output:** Startup diagnostics must show exactly which models are missing and how to fix.
3. **Configurable strictness:** Option to start with warnings only (e.g. for development) vs. hard fail.

## Validation Steps

### 1. Ollama reachability

- **Action:** `GET {OLLAMA_URL}/`
- **Success:** 200 OK, body contains "Ollama"
- **Failure:** Connection refused, timeout, non-2xx
- **Output:** `[OK] Ollama reachable at {url}` or `[FAIL] Ollama unreachable: {reason}`

### 2. List available models

- **Action:** `GET {OLLAMA_URL}/api/tags`
- **Success:** 200 OK, JSON `{ "models": [...] }`
- **Parse:** Extract model names (e.g. `name` or `model` field; Ollama returns `models[].name`)
- **Failure:** Non-2xx or invalid JSON
- **Output:** `[OK] Ollama models: {count} available` or `[FAIL] Could not list models: {reason}`

### 3. Check required models

For the active profile, collect models for: `chat`, `enrichment`, `embeddings`, and optionally `image_caption` (if configured).

- **Match logic:** Ollama returns names like `llama3.2:3b`. Config may specify `llama3.2:3b` or `llama3.2`. Match by prefix or exact (e.g. `llama3.2:3b` in list, or `llama3.2` matches `llama3.2:latest`).
- **Output per model:**
  - Present: `[OK] Model {role}: {model} (available)`
  - Missing: `[MISSING] Model {role}: {model} — run: ollama pull {model}`

### 4. Verdict

- **Strict mode (default in production):** If any required model is missing, exit with non-zero and print remediation.
- **Lenient mode (MESHMIND_MODEL_STRICT=false):** Log warnings, continue. Ask/embed will fail at runtime if model missing.

## Startup Output Example

```
MeshMind v2 Core starting...
[OK] Ollama reachable at http://localhost:11434
[OK] Ollama models: 3 available
[OK] Model chat: llama3.2:3b (available)
[OK] Model enrichment: llama3.2:3b (available)
[MISSING] Model embeddings: nomic-embed-text — run: ollama pull nomic-embed-text

Startup validation failed. Missing required models.
Set MESHMIND_MODEL_STRICT=false to start with warnings only.
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MESHMIND_MODEL_STRICT` | `true` | If true, fail startup when required models missing |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API URL |
| `MESHMIND_MODEL_PROFILE` | `cpu-friendly` | Profile for model selection |

## Implementation Notes

- Validation runs after config load, before HTTP server bind.
- Use `reqwest` or `ureq` for HTTP; keep timeout short (e.g. 5s).
- Model matching: Ollama `api/tags` returns `models[].name`; compare case-insensitively, support tag suffix (e.g. `:3b` vs `:latest`).
