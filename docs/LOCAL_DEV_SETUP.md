# MeshMind v2 — Local Development Setup

> **Note:** See [DEVELOPER_PREREQUISITES.md](DEVELOPER_PREREQUISITES.md) and [ENVIRONMENT_REPORT.md](ENVIRONMENT_REPORT.md) for environment details.

## Prerequisites

- Rust (MSVC on Windows), Node LTS, Python 3.11+, Docker, Ollama
- Developer PowerShell for VS 2022 (Windows native builds)

## Quick start

```powershell
# 1. Verify environment
.\scripts\check-env.ps1

# 2. Bootstrap
.\scripts\bootstrap.ps1

# 3. Run core (Developer PowerShell)
.\scripts\run.ps1

# 4. In another terminal: run UI (when implemented)
cd ui && npm install && npm run dev

# 5. Run worker (when implemented)
cd worker && pip install -r requirements.txt && python -m worker
```

## Project layout

```
meshmindv2/
├── crates/core/       # Rust core (API, storage, jobs)
├── ui/                # React SPA (future)
├── worker/            # Python worker (future)
├── scripts/           # check-env, bootstrap, run, test
├── docs/              # Foundation docs
└── data/              # Created by bootstrap (SQLite, etc.)
```

## Run/test commands

| Command | Purpose |
|---------|---------|
| `.\scripts\check-env.ps1` | Verify environment |
| `.\scripts\bootstrap.ps1` | Bootstrap repo |
| `.\scripts\run.ps1` | Start meshmind-core |
| `.\scripts\test.ps1` | Run tests |
| `.\scripts\test-rust-build.ps1` | Native build verification (Developer PS) |

## Docker (full stack)

```bash
docker compose up -d
```

(Compose file to be added when full stack is implemented.)

## Ports

| Service | Port |
|---------|------|
| Core | 3000 |
| UI | 5173 (Vite dev) |
| Ollama | 11434 |

## Environment variables

| Var | Purpose |
|-----|---------|
| `MESHMIND_PORT` | Core HTTP port (default 3000) |
| `MESHMIND_DB_PATH` | SQLite path (default `data/meshmind.db`) |
| `OLLAMA_URL` | Ollama base URL (default `http://localhost:11434`) |
