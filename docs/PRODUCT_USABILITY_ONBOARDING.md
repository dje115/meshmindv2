# Product Usability and Onboarding Phase

Summary of the UX/product improvements implemented before adding more connectors.

## UX/Product Improvements

### A. Visual/Product UX Pass

- **Design tokens**: Added CSS variables for surface, text, accent, and radius
- **Layout polish**: Refined header nav (rounded active states, spacing), main content padding
- **Overview as command centre**: Replaced placeholder with Quick actions (Add source, Ask, Search, Dashboards) and Recent jobs panel; stat cards with links; get-started CTA when empty
- **Empty states**: Upgraded EmptyState with optional hint, better visual treatment (rounded border, bg); used across Sources, Agents, Dashboards, Overview

### B. Sources Onboarding

- **Add Source flow**: New `/sources/add` route with full filesystem form
- **Form fields**: Source name, workspace, path, include/exclude patterns, enabled
- **Actions**: Save (creates source via API), Cancel; Test connection and Ingest now shown as disabled with note that backend API is required
- **Source detail**: Shows path from config, Test/Ingest placeholder actions

### C. Agents UX

- **State display**: online (active), offline/stale, dead with icons and color coding
- **Capabilities, last heartbeat, current/last job**: Shown in table (job from jobs list matched by agent_id)
- **Onboarding panel**: Collapsible help explaining what agents are, how to install/run/register, that host/machine is not yet in API

### D. Chat UX Foundation

- **Left sidebar**: Conversation list, New chat button
- **Session-backed threads**: `store/chat.ts` persists threads to sessionStorage
- **Starter prompts**: Four clickable prompts in empty state
- **Chat bubbles**: User (right, sky), assistant (left, slate) with citation cards below
- **Room for memory**: Architecture ready for future retention controls

### E. Dashboards Foundation

- **Nav**: Dashboards as first-class nav item
- **List + detail**: Dashboard list page, dashboard detail (including `/dashboards/new`)
- **Placeholder widgets**: Card shell and “Add widget” button
- **Docs**: `docs/DASHBOARDS.md` with publishable URLs, wallboard mode, per-dashboard permissions

### F. Settings Alignment

- **Sections**: General, Chat & Memory, Internet Research, Document Processing, Models, Workers & Jobs
- UI-first; no migration of env/config yet

## Backend/API Gaps

| Gap | Impact |
|-----|--------|
| **POST /api/sources/:id/ingest** | Test connection and Ingest now cannot run; UI shows placeholder |
| **Source test/validation endpoint** | No way to verify path or connectivity before ingest |
| **Agent host/machine** | Agents table cannot show which machine is running the worker |
| **Jobs by agent_id** | Jobs list filters by source_id, status, limit only; client-side match used for “current/last job” |
| **Dashboard CRUD** | Dashboards are UI-only; no persistence |
| **Chat persistence** | Threads in sessionStorage only; no server-side chat history |

## Tests

- **Unit**: `chat` store, AddSource form, EmptyState
- **Playwright**: create source, agents nav, ask/chat, dashboards, accessibility smoke

## Next Best Phase

**Connectors expansion** is the natural next step: add more source types (SharePoint, S3, etc.) now that the Add Source flow exists. Alternatively:

1. **Ingest API** – Implement POST `/sources/:id/ingest` so Test/Ingest actions work
2. **Chat persistence** – Backend chat threads and history for Ask
3. **Dashboard backend** – CRUD and widget model
