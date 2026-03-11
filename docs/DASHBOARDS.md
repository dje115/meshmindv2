# Dashboards

MeshMind v2 dashboards provide AI-powered analytics and visualizations over the knowledge base.

## Current State

- **UI shell**: Dashboard list and detail pages exist. Create-dashboard flow skeleton is in place.
- **Placeholder widgets**: Card layout for future widget types (charts, metrics, AI insights).
- **No backend yet**: Dashboards are UI-only; persistence and APIs are planned.

## Architecture Notes

### Publishable dashboard URLs

- Each dashboard will have a unique shareable URL.
- Optional read-only token for unauthenticated access.
- Configurable expiry for public links.

### Wallboard / public mode

- Full-screen, auto-refresh mode for displays.
- Minimal chrome; optimized for kiosks and TVs.
- Optional rotation across multiple dashboards.

### Per-dashboard permissions

- Dashboards will be scoped to workspaces.
- Role-based access: view vs edit.
- Future: share with specific users or groups.

### Widget model (planned)

- **Widget types**: Stat, Chart (bar, line, pie), Table, Text/Markdown.
- **Data sources**: Knowledge base metrics, source coverage, job stats, custom queries.
- **AI-generated**: Optional "suggest widgets" from natural language.

### Next steps

1. Add dashboard CRUD API and storage.
2. Implement widget model and rendering.
3. Add publishable URLs and permission model.
4. Optional: wallboard mode.
