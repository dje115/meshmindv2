# MeshMind v2 — Product Direction

> **Purpose:** Record product and architecture direction for MeshMind v2. These are design principles and planned feature areas—not current implementation scope.

---

## 1. UI-First Application Settings

**Principle:** The normal way to configure MeshMind should be through the Settings area in the web UI, not by manually editing config files.

### Design Rule

- Store operational and application settings in the database and expose them in the UI.
- Use config files / env vars only for:
  - bootstrap and first-run setup
  - secrets
  - infrastructure wiring
  - emergency recovery overrides
- As future phases are implemented, prefer admin-manageable settings screens over file-based configuration.

### Examples: UI-Managed (Eventual)

| Area | Examples |
|------|----------|
| Sources | source definitions, include/exclude rules |
| Ingest | ingest schedules |
| Document processing | OCR toggles, Tika endpoint and options |
| Models | model selection |
| Operations | retry policies, rate limits |
| Retention | retention rules |
| Workspaces | workspace settings |
| Agents | agent assignment rules |
| Search | search and ranking options |
| Web research | web/internet research policy and controls |
| Diagnostics | logging options where appropriate |

### Examples: Bootstrap / Env / Infrastructure Only

- `DATABASE_URL`
- JWT secret / signing keys
- bootstrap admin / initial setup secrets
- internal service ports
- low-level container wiring
- install-specific storage paths where necessary

---

## 2. Controlled Internet Research (Retained from v1 Intent)

**Principle:** MeshMind must retain controlled internet research capability as intended in v1.

### Use Cases

- research
- current fact-finding
- price finding
- product lookups
- external supporting information when local knowledge is insufficient

### Design Rule

- Treat web/internet research as a **controlled capability layer**, not uncontrolled always-on behavior.
- Configurable in the Settings UI.
- Support role/policy control, source transparency, citation, and auditability.
- MeshMind must distinguish local knowledge answers from externally researched answers.

---

## 3. ChatGPT-Style Conversation Experience

**Principle:** MeshMind chat must evolve toward a ChatGPT-style conversation experience, not just a search box.

### Design Direction

- Conversation threads
- Saved chats
- Chat history
- Contextual continuity within chats
- Optional controllable memory/context features
- Citations/provenance alongside answers
- Distinction between local-only, web-researched, and mixed answers
- Workspace-aware and role-aware chat behavior
- Future settings for memory, retention, and conversation controls

---

## 4. AI-Powered Dashboards (Planned Later)

**Principle:** MeshMind should later support AI-powered dashboards.

### Design Direction

- AI-assisted dashboards and summary views
- Dashboard widgets backed by local data, structured sources, and search/chat outputs
- Natural-language-assisted dashboard/report creation
- Provenance for dashboard insights where practical
- **Planned later feature area—not current implementation scope**

---

## Settings Migration (Future Phases)

### First-Wave UI-Managed Settings (Recommended Priority)

| Priority | Setting / Area | Current Location | Rationale |
|----------|----------------|------------------|-----------|
| 1 | Pagination defaults (jobs 20, audit 50) | handlers.rs | User-facing; simple to move |
| 2 | Per-source connector config (path, patterns, batch_size, rate_limit) | DB + connector | Core operational control |
| 3 | Model profile selection | config/meshmind-models.toml | User choice of models |
| 4 | Tika endpoint and timeout | env, tika_fallback.py | Document processing control |
| 5 | Job max_retries and backoff | workers.rs, jobs entity | Operational tuning |
| 6 | Heartbeat intervals (stale 90s, dead 300s) | workers.rs | Operational tuning |
| 7 | Ingest schedules | (not yet) | User-facing scheduling |
| 8 | Include/exclude rules | source config in DB | Already DB-backed; expose in UI |

### Remain Bootstrap / Env / Secret

- `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`
- `MESHMIND_CONFIG`, `MESHMIND_SEED_DEV_ADMIN`, `MESHMIND_CHANGE_STORE`
- Internal ports, container wiring

---

## Future Settings UI Structure (Conceptual)

### Settings Sections (Proposed)

| Section | Purpose | Key Settings |
|---------|---------|--------------|
| **General** | App-wide defaults | Pagination, timeouts, CORS |
| **Sources & Ingest** | Source definitions, schedules | Source config, include/exclude rules, ingest schedules |
| **Document Processing** | Extraction and processing | Tika endpoint, timeout, OCR toggles |
| **Models** | LLM and embedding selection | Model profile, OLLAMA_URL (or env fallback) |
| **Workers & Jobs** | Operational tuning | Retries, backoff, heartbeat intervals |
| **Search & Retrieval** | Search behavior | Chunk size, top-k, ranking, filters |
| **Chat & Memory** | Conversation and history | Chat retention, memory/context controls, workspace behavior |
| **Internet Research** | Web research capability | Enable/disable, policy, role controls, source transparency |
| **Retention & Storage** | Data lifecycle | Retention rules |
| **Diagnostics** | Logging and debugging | Log levels, debug options |

### Internet Research (Proposed Placement)

**Location:** Settings → **Internet Research** (dedicated section or under **Chat & Search**)

- Enable/disable web research capability
- Policy: allowed roles, allowed use cases (research, price lookup, etc.)
- Rate limits and quotas
- Source transparency (show which external sources were used)
- Citation and audit requirements
- Per-workspace overrides (if applicable)

### Chat History / Memory (Proposed Placement)

**Location:** Settings → **Chat & Memory** (or **Chat** under a broader **Conversation** area)

- Chat retention (how long to keep history)
- Memory/context controls (whether chat context is carried across turns)
- Workspace-aware behavior
- Per-user vs. per-workspace preferences (future)
- Export / archive options

### AI Dashboards (Proposed Placement)

**Location:** Future **Dashboards** area in main navigation (e.g., `/dashboards`)

- Create/edit dashboard
- Add widgets (local data, structured sources, search/chat outputs)
- Natural-language-assisted creation (later)
- Provenance per widget
- **Not a Settings subsection**—dashboards are first-class entities with their own screens; Settings may expose defaults (e.g., default widget types, refresh intervals)

---

## References

- [CONFIGURATION_AUDIT.md](CONFIGURATION_AUDIT.md) — Current settings inventory and migration plan
- [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md) — In-scope capabilities and non-goals
- [UI_SCREEN_LIST.md](UI_SCREEN_LIST.md) — Current and future screens
