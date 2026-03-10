# MeshMind v2 — Configuration Audit

> **Audit scope:** Settings, configuration values, operational options, dependency endpoints, feature toggles, and defaults. Goal: identify what should eventually move to Settings UI vs. remain bootstrap/infrastructure. See [PRODUCT_DIRECTION.md](PRODUCT_DIRECTION.md) for UI-first settings principle and future Settings UI structure.

---

## Settings Categories (Standard Naming)

| Category | Meaning | Examples |
|----------|---------|----------|
| **Bootstrap** | Infrastructure/dev setup only; not UI-managed | MESHMIND_CONFIG, MESHMIND_SEED_DEV_ADMIN, MESHMIND_CHANGE_STORE |
| **Secret / env only** | Must not be committed; use env or secrets manager | JWT_SECRET, DATABASE_URL, MEILISEARCH_API_KEY |
| **Planned for UI/DB** | Will move to Settings UI or database in future | Pagination defaults, per-source config, Tika endpoint, model profile |

**Standard variable:** `OLLAMA_URL` is the canonical Ollama base URL (not `MESHMIND_OLLAMA_URL`).

---

## 1. Environment Variables

| Name | Where | Default | Purpose | Current Source | Recommended Home | Change Soon? |
|------|-------|---------|---------|----------------|------------------|--------------|
| `CONTROL_API_PORT` | control-api config.rs | 3000 | HTTP bind port | Env | Bootstrap/config | No |
| `DATABASE_URL` | control-api config.rs | postgres://meshmind:meshmind@localhost:5432/meshmind | Postgres connection | Env | Secret/env only | No |
| `REDIS_URL` | control-api config.rs | redis://localhost:6379 | Redis connection | Env | Secret/env only | No |
| `OLLAMA_URL` | control-api config.rs | http://localhost:11434 | Ollama API base | Env | Settings UI (or env) | No – not yet used |
| `JWT_SECRET` | control-api config.rs | "change-me-in-production" | JWT signing | Env | Secret/env only | **Yes** – document |
| `MESHMIND_SEED_DEV_ADMIN` | control-api config.rs, db.rs | false | Create admin user on startup | Env | Bootstrap only | No |
| `MESHMIND_CONFIG` | control-api config.rs | meshmind.toml | Config file path | Env | Bootstrap only | No |
| `RUST_LOG` | main.rs (EnvFilter) | info | Tracing log level | Env | Bootstrap only | No |
| `CONTROL_API_URL` | worker-runtime config | http://localhost:3000 | Control plane URL | Env | Bootstrap/config | No |
| `MESHMIND_AGENT_ID` | worker-runtime config | (none) | Pre-registered agent ID | Env | Bootstrap | No |
| `MESHMIND_AGENT_NAME` | worker-runtime config | meshmind-worker | Agent name | Env | Bootstrap | No |
| `MESHMIND_AGENT_CAPABILITIES` | worker-runtime config | filesystem | Capability list | Env | Bootstrap | No |
| `MESHMIND_HEARTBEAT_INTERVAL_SECS` | worker-runtime config | 30 | Heartbeat interval | Env | Settings UI or bootstrap | No |
| `MESHMIND_CLAIM_INTERVAL_SECS` | worker-runtime config | 5 | Job claim poll interval | Env | Settings UI or bootstrap | No |
| `MESHMIND_CHANGE_STORE` | worker-connectors main | data/connector-state/{source_id}.json | Change detection state path | Env | Bootstrap/config | No |
| `TIKA_SERVER_ENDPOINT` | docproc tika_fallback | http://localhost:9998 | Apache Tika REST URL | Env | Settings UI or bootstrap | No |
| `TIKA_TIMEOUT_SECS` | docproc tika_fallback | 60 | Tika request timeout | Env | Settings UI or bootstrap | No |
| `LOG_LEVEL` | docproc cli | INFO | Log level | Env | Bootstrap | No |
| `MESHTEST_PATH` | docproc tests | (none) | Optional integration test path | Env | Test-only | No |
| `QDRANT_URL` | .env.example | http://localhost:6333 | Qdrant base URL | Env (doc) | Settings UI or env | Not yet used |
| `MEILISEARCH_URL` | .env.example | http://localhost:7700 | Meilisearch base | Env (doc) | Settings UI or env | Not yet used |
| `MEILISEARCH_API_KEY` | .env.example | dev-key-minimum-32-characters-long | Meilisearch key | Env (doc) | Secret/env only | Not yet used |
| `MESHMIND_MODEL_PROFILE` | docs only | cpu-friendly | Model profile name | (Not wired) | Settings UI | Future |
| `MESHMIND_MODELS_CONFIG` | docs only | config/meshmind-models.toml | Model config path | (Not wired) | Bootstrap | Future |
| ~~MESHMIND_OLLAMA_URL~~ | (deprecated) | — | Use `OLLAMA_URL` instead |

---

## 2. Config Files

| File | Purpose | Format | Loaded By | Recommended Home |
|------|---------|--------|-----------|------------------|
| `config/meshmind-models.toml` | Model profiles (chat, enrichment, embeddings) | TOML | (Not wired) | Settings UI / DB |
| `config/meshmind-models.example.toml` | Example model config | TOML | Manual copy | Bootstrap |
| `meshmind.toml` | Control-api config (optional) | TOML | config.rs if exists | Bootstrap |
| `apps/worker-connectors/examples/filesystem-config.example.json` | Example source config | JSON | Docs/example | Bootstrap |
| Source config (DB) | path, include_patterns, exclude_patterns, max_depth, batch_size, rate_limit_delay_secs | JSON | Connector from job | Settings UI / DB |

---

## 3. Hard-Coded Defaults in Code

| Setting | Location | Value | Purpose | Recommended |
|---------|----------|-------|---------|-------------|
| `http_bind` fallback | config.rs | 0.0.0.0:3000 | Bind address | Env override |
| `data_dir` | config.rs | ./data | Data directory | Env or config |
| `cors_enabled` | config.rs | true | CORS | Config/UI |
| `jwt_secret` default | config.rs | "change-me-in-production" | Dev default | Must be env in prod |
| `HEARTBEAT_STALE_SECS` | workers.rs | 90 | Agent stale threshold | Config or env |
| `HEARTBEAT_DEAD_SECS` | workers.rs | 300 | Agent dead threshold | Config or env |
| `AGENT_STATUS_CLEANUP_INTERVAL_SECS` | main.rs | 60 | Cleanup task interval | Config |
| `max_retries` (job) | jobs entity, migrations | 3 | Job retry limit | DB default; UI override |
| Retry backoff base | workers.rs | 30 * (1 << retry_count) | Exponential backoff | Config |
| `default_limit` (jobs list) | handlers.rs | 20 | Jobs list page size | UI/settings |
| `default_audit_limit` | handlers.rs | 50 | Audit list page size | UI/settings |
| Jobs list limit clamp | jobs.rs | 1..100 | Max limit | Keep or UI |
| `DEFAULT_TIKA_ENDPOINT` | tika_fallback.py | http://localhost:9998 | Tika URL | Env |
| `DEFAULT_TIMEOUT` | tika_fallback.py | 60.0 | Tika timeout | Env |
| `MIN_CHARS_PER_PAGE` | pdf.py | 50 | PDF readable threshold | Config (later) |
| `MIN_TOTAL_CHARS` | pdf.py | 100 | PDF readable threshold | Config (later) |
| `jwt_ttl_secs` | auth.rs | 86400 (24h) | JWT expiry | Config or env |
| Worker client timeout | client.py | 30.0 | HTTP timeout | Config |
| Vite proxy `/api` | vite.config.ts | http://localhost:3000 | Dev API proxy | Dev-only |
| Vite server port | vite.config.ts | 5173 | Dev server port | Dev-only |

---

## 4. Dependency/Service Endpoints

| Service | Env / Config | Default | Used By |
|---------|--------------|---------|---------|
| Postgres | DATABASE_URL | localhost:5432 | control-api |
| Redis | REDIS_URL | localhost:6379 | control-api (config only; not yet used) |
| Qdrant | QDRANT_URL | localhost:6333 | .env.example only |
| Meilisearch | MEILISEARCH_URL | localhost:7700 | .env.example only |
| Ollama | OLLAMA_URL | localhost:11434 | control-api (config only; not yet used) |
| Apache Tika | TIKA_SERVER_ENDPOINT | localhost:9998 | docproc worker |
| Control API | CONTROL_API_URL | localhost:3000 | workers |

---

## 5. Operational Timeouts / Retry Values

| Setting | Location | Value | Recommended Home |
|---------|----------|-------|------------------|
| Job max_retries | DB + workers.rs | 3 | DB default; Settings UI |
| Job retry backoff | workers.rs | 30s, 60s, 120s... | Config or Settings UI |
| Heartbeat stale | workers.rs | 90s | Config |
| Heartbeat dead | workers.rs | 300s | Config |
| Agent cleanup interval | main.rs | 60s | Config |
| Tika timeout | tika_fallback.py | 60s | Env or config |
| Worker HTTP timeout | client.py | 30s | Config |
| Filesystem rate_limit_delay_secs | connector config | 0.1 | Source config (DB) |

---

## 6. Feature Flags / Capability Toggles

| Setting | Location | Purpose | Recommended |
|---------|----------|---------|-------------|
| `seed_dev_admin` | config.rs | Create admin on startup | Bootstrap only |
| `cors_enabled` | config.rs | Enable CORS | Config |
| Worker capabilities | agent_capabilities table | filesystem, docproc, ocr, image, embed | DB; UI-managed |
| job_kind | jobs table | docproc, image, ocr | DB; system |

---

## 7. Model-Related Settings

| Setting | Location | Status | Recommended Home |
|---------|----------|--------|------------------|
| `meshmind-models.toml` | config/ | Documented, not wired | Settings UI / DB |
| `MESHMIND_MODEL_PROFILE` | docs | Documented, not wired | Settings UI |
| `MESHMIND_MODELS_CONFIG` | docs | Documented, not wired | Bootstrap |
| `MESHMIND_OLLAMA_URL` | docs | Duplicate of OLLAMA_URL | Consolidate to OLLAMA_URL |
| Per-role overrides | docs | MESHMIND_MODEL_CHAT etc. | Future; Settings UI |

---

## 8. Connector-Related Settings

| Setting | Source | Default | Recommended |
|---------|--------|---------|-------------|
| path | Source config (DB) | (required) | UI (source config) |
| include_patterns | Source config | [] | UI |
| exclude_patterns | Source config | node_modules, .git | UI |
| max_depth | Source config | -1 | UI |
| batch_size | Source config | 100 | UI |
| rate_limit_delay_secs | Source config | 0.1 | UI |
| MESHMIND_CHANGE_STORE | Env | data/connector-state/{id}.json | Bootstrap |

---

## 9. Security / Auth Settings

| Setting | Location | Default | Recommended |
|---------|----------|---------|-------------|
| JWT_SECRET | config.rs | "change-me-in-production" | Secret/env only; required in prod |
| jwt_ttl_secs | auth.rs | 86400 | Config or env |
| Argon2 params | users.rs, auth.rs | Argon2::default() | Keep; document |
| agent_token | DB | Plain text | Document; hash later (TODO) |

---

## 10. Paths / Storage / Runtime

| Setting | Location | Default | Recommended |
|---------|----------|---------|-------------|
| data_dir | config.rs | ./data | Bootstrap |
| MESHMIND_CHANGE_STORE | worker-connectors | data/connector-state/{id}.json | Bootstrap |
| meshmind.toml path | MESHMIND_CONFIG | meshmind.toml | Bootstrap |
| meshmind-models path | MESHMIND_MODELS_CONFIG | config/meshmind-models.toml | Bootstrap |

---

## 11. Docker / Container Settings

| Setting | File | Value | Affects |
|---------|------|-------|---------|
| Postgres env | docker-compose | POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB | DB credentials |
| Meilisearch | docker-compose | MEILI_MASTER_KEY, MEILI_ENV | Search |
| control-api env | docker-compose.yml | PORT, DATABASE_URL, REDIS_URL, OLLAMA_URL | Runtime |
| Health check intervals | docker-compose | 5s, 10s | Startup |
| Web port | docker-compose | 8080:80 | Web access |

---

## 12. Web / Tika / Ollama / OCR

| Component | Settings | Status |
|-----------|----------|--------|
| Web (Vite) | port 5173, proxy to 3000 | Dev only |
| Tika | TIKA_SERVER_ENDPOINT, TIKA_TIMEOUT_SECS | Env; docproc |
| Ollama | OLLAMA_URL | Config; not yet used |
| OCR | (none) | Placeholder |

---

## Duplicates and Conflicts

| Issue | Detail |
|-------|--------|
| OLLAMA_URL vs MESHMIND_OLLAMA_URL | Docs mention MESHMIND_OLLAMA_URL; code uses OLLAMA_URL. Use OLLAMA_URL only. |
| .env.example vs infrastructure/.env.example | Root .env.example omits JWT_SECRET, MESHMIND_SEED_DEV_ADMIN. infra/.env.example omits these too. Both should document required vars. |
| CORS | cors_enabled in config but not obviously used in router. Verify usage. |

---

## Implicit Settings to Make Explicit

| Setting | Current | Recommendation |
|---------|---------|----------------|
| Job list max limit | Hard clamp 1..100 in jobs.rs | Document or make configurable |
| PDF readable thresholds | Constants in pdf.py | Env or config for tuning |
| JWT TTL | Hard-coded 24h | Env JWT_TTL_SECS |
| Agent stale/dead thresholds | Constants in workers.rs | Env or config |

---

## Missing But Needed (Addressed in Configuration Hygiene)

| Setting | Status |
|---------|--------|
| JWT_SECRET in .env.example | Done |
| MESHMIND_SEED_DEV_ADMIN in .env.example | Done |
| TIKA_* in .env.example | Done |
| CONTROL_API_URL, worker vars in .env.example | Done |

---

## Categorized Table (All Discovered Settings)

| Category | Count | Examples |
|----------|-------|----------|
| Env vars | 24+ | DATABASE_URL, JWT_SECRET, TIKA_SERVER_ENDPOINT |
| Config files | 4 | meshmind-models.toml, meshmind.toml |
| Hard-coded | 20+ | HEARTBEAT_STALE_SECS, default_limit 20 |
| Endpoints | 7 | Postgres, Redis, Tika, Ollama, etc. |
| Timeouts/retries | 8 | Tika 60s, worker 30s, job backoff |
| Feature toggles | 4 | seed_dev_admin, cors, capabilities |
| Model settings | 5 | Profiles, OLLAMA_URL (unused) |
| Connector settings | 6 | path, batch_size, rate_limit_delay |
| Security | 4 | JWT_SECRET, ttl, Argon2 |
| Paths/storage | 4 | data_dir, change store |
| Docker | 6+ | Postgres creds, ports, health |

---

## Recommended Migration Plan

### Phase 1 — Bootstrap / Env Only (no code change)

- Add JWT_SECRET, MESHMIND_SEED_DEV_ADMIN, TIKA_* to .env.example.
- Consolidate .env.example and infrastructure/.env.example (or cross-reference).
- Document OLLAMA_URL as canonical; remove MESHMIND_OLLAMA_URL from docs.

### Phase 2 — Move to Settings UI (future)

1. **High priority (user-facing)**  
   - Pagination defaults (jobs limit 20, audit limit 50)  
   - Per-source connector config (path, patterns, batch_size, rate_limit)  
   - Model profile selection (when wired)  

2. **Medium priority**  
   - Job max_retries and backoff  
   - Heartbeat intervals (stale 90s, dead 300s)  
   - Tika endpoint and timeout  

3. **Low priority**  
   - Agent cleanup interval  
   - CORS toggle  

### Phase 3 — Remain Env / Config Only

- DATABASE_URL, REDIS_URL, JWT_SECRET (secrets)
- MESHMIND_CONFIG, MESHMIND_MODELS_CONFIG (paths)
- MESHMIND_SEED_DEV_ADMIN (bootstrap)
- MESHMIND_CHANGE_STORE (connector bootstrap)

---

## Internet / Web Research Settings (Future)

MeshMind will retain controlled internet research (see [PRODUCT_DIRECTION.md](PRODUCT_DIRECTION.md)). Settings needed when implemented:

| Setting | Purpose |
|---------|---------|
| QDRANT_URL | Vector DB for embeddings |
| MEILISEARCH_URL, MEILISEARCH_API_KEY | Full-text search |
| Embedding model | From model config |
| Chunk size / overlap | Retrieval tuning |
| Top-k / rerank | Search results |
| Search filters | By source, workspace |
| API rate limits | Per user/tenant |

---

## Biggest Configuration Problems

1. **JWT_SECRET default** — Hard-coded "change-me-in-production"; must be overridden in production. Not clearly documented in .env.example.
2. **Split env examples** — .env.example and infrastructure/.env.example are inconsistent; JWT_SECRET and TIKA_* missing from both.
3. **OLLAMA_URL unused** — In config but not in AppState; ollama not used yet. Documented model vars (MESHMIND_MODEL_*, MESHMIND_OLLAMA_URL) are not wired.
4. **Scattered worker settings** — Worker runtime, connectors, and docproc each read different env vars; no single reference.
5. **Hard-coded operational values** — Heartbeat (90s/300s), job backoff, JWT TTL, PDF thresholds not configurable.

---

## Future UI-Managed Settings Direction

When implementing the Settings UI: **High priority** — Pagination defaults (jobs 20, audit 50), per-source connector config, model profile. **Medium** — Job max_retries/backoff, heartbeat intervals, Tika endpoint/timeout. **Remain env/secret** — DATABASE_URL, JWT_SECRET, MESHMIND_SEED_DEV_ADMIN, MESHMIND_CHANGE_STORE. See Recommended Migration Plan (Phase 2) below.

---

## Configuration Hygiene (Completed)

1. **Unified .env.example:**
   - JWT_SECRET, MESHMIND_SEED_DEV_ADMIN, TIKA_*, CONTROL_API_URL and worker vars documented.
2. **Docs:** OLLAMA_URL standardized; MESHMIND_OLLAMA_URL deprecated. See Settings Categories and Future UI-Managed Settings above.
