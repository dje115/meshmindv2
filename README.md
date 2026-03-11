# MeshMind v2

**On-prem, server-first, browser-first AI knowledge platform.** Ingest documents and structured data, search and answer questions using local LLMs. Data stays on your infrastructure.

**Repository:** [github.com/dje115/meshmindv2](https://github.com/dje115/meshmindv2)

## Architecture

- **control-api** (Rust) — Main control plane. Orchestrates workers, sources, search, chat.
- **web** (React + TypeScript + Tailwind) — Browser UI.
- **Workers** (Python) — docproc, OCR, image, embed, connectors (filesystem first).
- **Infrastructure** — Postgres, Redis, Qdrant, Meilisearch, Ollama.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/adr/ADR-005-server-first-worker-based.md](docs/adr/ADR-005-server-first-worker-based.md).

## Quick start

### Prerequisites

- Rust, Node.js 22+, Python 3.11+
- Docker (for Postgres, Redis, Qdrant, Meilisearch)

### Run locally

```bash
# 1. Start infrastructure (Postgres, Redis, Qdrant, Meilisearch)
make infra-up
# or: docker compose -f infrastructure/docker-compose.infra.yml up -d

# 2. Copy env
cp .env.example .env

# 3. Run control-api (terminal 1)
make control-api
# or: cargo run -p meshmind-control-api

# 4. Run query-api (terminal 2)
make query-api
# or: cd apps/query-api && python -m meshmind_query_api

# 5. Run web (terminal 3)
make web
# or: cd apps/web && npm run dev
```

- Control API: http://localhost:3000
- Query API: http://localhost:3001
- Web: http://localhost:5173
- Health: http://localhost:3000/health

### Environment variables (control-api)

| Var | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | — | Postgres connection string (required) |
| `JWT_SECRET` | — | JWT signing secret (required) |
| `QUERY_API_URL` | — | Query API base URL (e.g. http://localhost:3001) |
| `OLLAMA_URL` | http://localhost:11434 | Ollama API URL |
| `MESHMIND_SEED_DEV_ADMIN` | false | Seed admin user (username/password: admin/admin) |

### Full stack via Docker

```bash
make full-up
# or: docker compose -f infrastructure/docker-compose.yml up -d
# control-api: 3000, web: 8080
```

## Filesystem connector (ingestion)

```bash
# Terminal 4: run the filesystem connector to process ingest jobs
pip install -e apps/worker-runtime -e apps/worker-connectors
CONTROL_API_URL=http://localhost:3000 MESHMIND_AGENT_NAME=meshmind-fs-connector MESHMIND_AGENT_CAPABILITIES=filesystem,docproc python apps/worker-connectors/main.py
```

Create a filesystem source in the web UI (Sources → Add source), trigger ingest, and the connector will scan and process files.

**Troubleshooting:** If jobs get stuck in `claimed` (e.g. connector crashed), reset them with `python scripts/reset_stuck_jobs.py` or `POST /api/jobs/reset-stuck`.

## Folder layout

```
apps/
  control-api/     # Rust API (axum, tokio, sqlx)
  web/             # React SPA (Vite, Tailwind)
  worker-runtime/  # Python shared worker framework
  worker-docproc/  # Document processing
  worker-ocr/      # OCR
  worker-image/    # Image processing
  worker-embed/    # Embeddings (placeholder)
  worker-connectors/  # Connectors (filesystem first)

packages/
  contracts/       # OpenAPI + JSON Schemas
  docs/            # Links to /docs
  scripts/         # Task runner

infrastructure/
  docker-compose.yml
  .env.example

docs/              # Foundation docs, ADRs
scripts/           # Env checks, bootstrap, reset_stuck_jobs.py
```

## Project status (through Phase 4)

- **Control plane**: Worker protocol (register, heartbeat, claim, complete, fail), source items, jobs, claim includes source_item for docproc.
- **Worker runtime**: Shared Python framework for workers.
- **Filesystem connector**: Scan, change detection, provenance, submit items, dispatch docproc/image jobs.
- **Document processing worker**: Extraction for PDF, DOCX, DOC, XLSX, XLS, TXT, MD, RTF, HTML, CSV, JSON. PDF readable-vs-OCR detection. Legacy Office (.doc, .xls) via Apache Tika.

## Supported file types (document processing)

| Type | Parser |
|------|--------|
| PDF | pypdf (OCR fallback when sparse text) |
| DOCX | python-docx |
| DOC | Apache Tika (requires Tika server) |
| XLSX | openpyxl |
| XLS | xlrd; Tika fallback on failure |
| TXT, MD, RTF, HTML, CSV, JSON | Native parsers |

**Apache Tika** is required for `.doc` and some `.xls` cases. Run `docker run -d -p 9998:9998 apache/tika:latest` or a Tika JAR. Set `TIKA_SERVER_ENDPOINT=http://localhost:9998`.

## Testing

```bash
# Rust
cargo test -p meshmind-control-api

# Document processing (Python)
pip install -e apps/worker-runtime -e "apps/worker-docproc[dev]"
cd apps/worker-docproc && python -m pytest -v

# Filesystem connector
pip install -e apps/worker-runtime -e apps/worker-connectors
cd apps/worker-connectors && python -m pytest -v
```

Optional integration tests: set `MESHTEST_PATH` to a folder with Office samples for docproc legacy tests.

## Documentation

- [Documentation index](docs/INDEX.md)
- [Changelog](CHANGELOG.md)
- [Local dev setup](docs/LOCAL_DEV_SETUP.md)
- [Worker protocol](docs/WORKER_PROTOCOL.md)
- [Filesystem connector](docs/FILESYSTEM_CONNECTOR.md)
- [Document processing](docs/DOCUMENT_PROCESSING.md)

## License

MIT
