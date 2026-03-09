# MeshMind v2 — UI Screen List

> **Note:** v1 used a Tauri desktop app. v2 is browser-first with a React SPA.

## Screens (MVP)

| Screen | Route | Purpose |
|--------|-------|---------|
| **Login** | `/login` | Sign in (username/password or API key) |
| **Dashboard** | `/` or `/dashboard` | Overview: source count, job status, recent activity |
| **Ask** | `/ask` | Question input, answer with citations |
| **Search** | `/search` | Full-text/semantic search, results with provenance |
| **Sources** | `/sources` | List sources, add source, trigger ingest |
| **Jobs** | `/jobs` | List ingest/embed jobs, status, errors |
| **Admin** | `/admin` | Users, roles, workers (if admin role) |

## Future (post-MVP)

| Screen | Route | Purpose |
|--------|-------|---------|
| Source detail | `/sources/:id` | Edit source, view ingest history |
| Job detail | `/jobs/:id` | Logs, artifacts produced |
| Settings | `/settings` | User preferences, API keys |

## Navigation

- Top nav: Dashboard | Ask | Search | Sources | Jobs | (Admin if permitted)
- User menu: Profile, Logout

## Data dependencies per screen

| Screen | API endpoints |
|--------|---------------|
| Login | POST /auth/login |
| Dashboard | GET /api/stats, GET /api/jobs?limit=10 |
| Ask | POST /api/ask |
| Search | GET /api/search?q= |
| Sources | GET /api/sources, POST /api/sources, POST /api/sources/:id/ingest |
| Jobs | GET /api/jobs |
| Admin | GET /api/users, GET /api/roles, GET /api/workers |
