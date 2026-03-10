# MeshMind v2 Web App

## UI information architecture

| Route | Page | Purpose |
|-------|------|---------|
| `/login` | Login | Sign in (username/password) |
| `/` | Overview | Dashboard: sources, jobs, agents stats; recent jobs |
| `/search` | Search | Hybrid search with provenance; citation cards |
| `/ask` | Ask | ChatGPT-style Q&A; grounded answers with citations |
| `/explorer` | Knowledge Explorer | Browse sources and indexed content |
| `/sources` | Sources | List sources; drill to source detail |
| `/sources/:id` | Source Detail | Source metadata, config |
| `/agents` | Agents | List agents (live refresh); drill to agent detail |
| `/agents/:id` | Agent Detail | Agent status, capabilities |
| `/jobs` | Jobs | List jobs with filter; live refresh; drill to job detail |
| `/jobs/:id` | Job Detail | Job status, logs |
| `/workspaces` | Workspaces & Permissions | List workspaces |
| `/models` | Models | Model configuration (planned) |
| `/settings` | Settings | Application settings (UI-first direction) |

## Features

- **Search & Ask**: ChatGPT-style UX; Search results and Ask citations show filename, page/sheet reference, "Open original file" when available.
- **Provenance drawer**: View provenance (filename, path, open target) from search results and citations.
- **Document preview panel**: View document chunks.
- **Role-aware navigation**: Full nav for authenticated users.
- **Error boundaries**, loading/empty states, data tables with filters.
- **Backend enrichment**: Search and citation payloads include `filename` and `open_target` from provenance when available (chunk_index, metadata).

## How to run against local services

See [apps/web/README.md](../apps/web/README.md).

## Follow-on adjustments before Microsoft/business connectors

- **Source creation**: Add UI to create sources (filesystem, connectors). Control-api has `POST /sources`; wire a form.
- **Ingest trigger**: Add "Ingest" action per source. Requires ingest endpoint in control-api.
- **Workspace filter**: Add workspace filter to Search/Ask when user has multiple workspaces.
- **Admin screens**: Users, Roles management (admin-only).
- **Connector-specific config**: UI for connector config (e.g. path for filesystem, OAuth for Microsoft).
