# ADR-004: Local Model Runtime (Ollama)

## Status

Accepted.

## Context

v2 is on-prem; we need an LLM runtime that runs locally without cloud dependencies. v1 supported Ollama and mock backends.

## Decision

- **Ollama:** Use Ollama as the local inference runtime for v2.
- **Core calls Ollama:** Core (Rust) invokes Ollama via HTTP for generate and embed.
- **No worker inference for Ask:** The Ask flow is Core → Ollama; workers may call Ollama for embeddings only if that responsibility is delegated.
- **Configurable URL:** `OLLAMA_URL` env var (default `http://localhost:11434`).

## Consequences

- No cloud API keys; all inference on-prem.
- Ollama must be running (or reachable) for Ask and embeddings.
- Model selection (e.g. llama3.2) is a deployment concern; Core can pass model name to Ollama.
- If Ollama is unavailable, Ask and embed operations fail; health check can report Ollama status.

## References

- ARCHITECTURE.md
- LOCAL_DEV_SETUP.md
- PRODUCT_SCOPE.md (local LLM assumption)
