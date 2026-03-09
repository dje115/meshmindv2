# MeshMind v2 — Model Configuration

MeshMind v2 uses a pluggable model configuration layer. Each role (chat, enrichment, embeddings, image-caption) can be assigned a different Ollama model.

## Model Roles

| Role | Purpose | Typical use |
|------|---------|-------------|
| **chat** | Grounded Q&A, answer generation with citations | Ask flow, user questions |
| **enrichment** | Summarization, classification, extraction | Document categorization, metadata |
| **embeddings** | Vector embeddings for semantic search | Hybrid search, retrieval |
| **image-caption** | Image description (optional) | Future: image indexing |

## Configuration Files

### Primary config: `config/meshmind-models.toml`

```toml
# MeshMind v2 - Model configuration
# Override via MESHMIND_MODEL_PROFILE env var (default: cpu-friendly)

[default]
profile = "cpu-friendly"

[profiles.cpu-friendly]
chat = "llama3.2:3b"
enrichment = "llama3.2:3b"
embeddings = "nomic-embed-text"
# image_caption = "llava:7b"   # optional; omit if not needed

[profiles.better-quality]
chat = "llama3.2"
enrichment = "mistral:7b"
embeddings = "nomic-embed-text"
# image_caption = "llava:13b"
```

### Per-environment override

Set `MESHMIND_MODEL_PROFILE` to select a profile:

```bash
# Use CPU-friendly (default)
export MESHMIND_MODEL_PROFILE=cpu-friendly

# Use better-quality on stronger hardware
export MESHMIND_MODEL_PROFILE=better-quality
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MESHMIND_OLLAMA_URL` | `http://localhost:11434` | Ollama API base URL |
| `MESHMIND_MODEL_PROFILE` | `cpu-friendly` | Profile name from meshmind-models.toml |
| `MESHMIND_MODELS_CONFIG` | `config/meshmind-models.toml` | Path to model config file |

### Per-role overrides (optional)

Override a single role without changing profile:

| Variable | Example | Description |
|----------|---------|-------------|
| `MESHMIND_MODEL_CHAT` | `phi3:mini` | Override chat model |
| `MESHMIND_MODEL_ENRICHMENT` | `mistral:7b` | Override enrichment model |
| `MESHMIND_MODEL_EMBEDDINGS` | `nomic-embed-text` | Override embeddings model |
| `MESHMIND_MODEL_IMAGE_CAPTION` | `llava:7b` | Override image-caption (optional) |

## Recommended Default Models

### Chat / Grounded answer

| Model | Size | Hardware | Notes |
|-------|------|----------|-------|
| `llama3.2:1b` | ~1.3 GB | CPU-only | Fastest; lower quality |
| `llama3.2:3b` | ~2.0 GB | CPU or modest GPU | Balanced; good default |
| `phi3:mini` | ~2.2 GB | CPU-friendly | Strong reasoning, compact |
| `llama3.2` | ~4.7 GB | GPU preferred | Higher quality |
| `mistral:7b` | ~4.1 GB | GPU | Good for classification |

### Enrichment / Classification

| Model | Size | Hardware | Notes |
|-------|------|----------|-------|
| `llama3.2:3b` | ~2.0 GB | CPU | Same as chat for simplicity |
| `phi3:mini` | ~2.2 GB | CPU | Good at structured extraction |
| `mistral:7b` | ~4.1 GB | GPU | Better summarization |

### Embeddings

| Model | Size | Hardware | Notes |
|-------|------|----------|-------|
| `nomic-embed-text` | ~274 MB | CPU/GPU | Standard; 2K context |
| `nomic-embed-text:latest` | ~274 MB | CPU/GPU | Same, explicit tag |

Ollama does not ship a wide variety of embedding models; `nomic-embed-text` is the recommended default.

### Image caption (optional)

| Model | Size | Hardware | Notes |
|-------|------|----------|-------|
| `llava:7b` | ~4.5 GB | GPU | Vision + text |
| `llava:13b` | ~8 GB | GPU | Higher quality |

Image-caption is optional; omit from config if not used.

## Default Profiles

### `cpu-friendly` (small business / development)

- **chat:** `llama3.2:3b`
- **enrichment:** `llama3.2:3b`
- **embeddings:** `nomic-embed-text`

Suitable for CPU-only or systems with limited GPU (e.g. 4 GB VRAM).

### `better-quality` (stronger hardware)

- **chat:** `llama3.2`
- **enrichment:** `mistral:7b`
- **embeddings:** `nomic-embed-text`

Suitable for 8+ GB VRAM or high-end CPU.

## Health Checks

MeshMind Core performs:

1. **Ollama reachability:** GET `{OLLAMA_URL}/` — must return 200
2. **Model availability:** GET `{OLLAMA_URL}/api/tags` — each configured model must be present in the response

Startup diagnostics report which models are missing. See [STARTUP_VALIDATION_DESIGN.md](STARTUP_VALIDATION_DESIGN.md).
