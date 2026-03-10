# MeshMind v2 — Ollama Setup

Ollama is the local model runtime for MeshMind v2. This document covers installation, configuration, and verification.

## Detection

### Is Ollama installed?

```powershell
# Windows
ollama --version
```

```bash
# Linux/macOS
ollama --version
```

If the command is not found, install Ollama from https://ollama.ai

### Is Ollama running?

Ollama runs as a background service. On first `ollama run <model>`, it starts automatically. For headless use (API only):

```powershell
# Windows - start Ollama (runs as service or app)
# If installed via installer, it auto-starts. Otherwise:
ollama serve   # Runs in foreground; use for development
```

```bash
# Linux - systemd
sudo systemctl status ollama

# macOS - LaunchAgent (auto-started on first use)
# Or: ollama serve
```

**API health check:** `GET http://localhost:11434/` returns "Ollama is running" (200 OK).

**List models:** `GET http://localhost:11434/api/tags` returns `{ "models": [...] }`.

## Installation

### Windows

1. Download from https://ollama.ai/download/windows
2. Run installer; Ollama runs as a background app
3. Or via winget: `winget install Ollama.Ollama`

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS

Download from https://ollama.ai/download/mac or use Homebrew: `brew install ollama`

## Pulling Models

Models are pulled on first use, or explicitly:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama pull phi3:mini
```

See [MODEL_CONFIGURATION.md](MODEL_CONFIGURATION.md) for recommended models by role and profile.

## Helper Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ollama-check.ps1` | Verify Ollama installed, running, list models |
| `scripts/ollama-check.sh` | Same for Linux/macOS |
| `scripts/ollama-pull-models.ps1` | Pull models for a profile (cpu-friendly, better-quality) |
| `scripts/ollama-pull-models.sh` | Same for Linux/macOS |

Usage:

```powershell
.\scripts\ollama-check.ps1
.\scripts\ollama-pull-models.ps1 -Profile cpu-friendly
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | (Ollama default) | Ollama listens on; e.g. `0.0.0.0` for network access |
| `OLLAMA_ORIGINS` | `*` | CORS origins for Ollama API |
| `OLLAMA_URL` | `http://localhost:11434` | MeshMind control-api uses this to call Ollama |
| `MESHMIND_MODEL_PROFILE` | `cpu-friendly` | Profile name from model config |

## Local Development

1. Ensure Ollama is installed and running.
2. Pull required models for your profile:
   ```powershell
   .\scripts\ollama-pull-models.ps1 -Profile cpu-friendly
   ```
3. Set `OLLAMA_URL` if Ollama is not on localhost.
4. Run MeshMind Core; startup validation will report model availability.

## Troubleshooting

| Issue | Action |
|-------|--------|
| `ollama` not found | Install from https://ollama.ai |
| Connection refused to 11434 | Start Ollama: `ollama serve` or restart the Ollama app |
| Model not found | Run `ollama pull <model>`; see MODEL_CONFIGURATION.md |
| Slow on CPU | Use `cpu-friendly` profile; consider smaller models (llama3.2:1b, phi3:mini) |
| Out of memory | Use smaller models or reduce context; close other GPU apps |
