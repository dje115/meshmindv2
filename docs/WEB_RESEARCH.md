# Controlled Web Research for MeshMind Ask

## Summary of Implementation

### What Was Implemented

1. **Web research service** (`apps/query-api/src/meshmind_query_api/services/web_research.py`)
   - Search via DuckDuckGo (no API key)
   - Fetch top results with httpx
   - Extract main text with trafilatura
   - Returns structured `WebCitation` (title, source, url, snippet)

2. **Routing logic** (`ask_service.py`)
   - **local**: Strong local results (RRF score ≥ 0.01) → answer from documents only
   - **web**: Weak/empty local + question seems external (keywords: current, today, latest, price, what is, etc.) → web search and answer from web
   - **mixed**: Strong local and question external → both contexts, LLM cites both

3. **API response**
   - `answer_source_type`: `local` | `web` | `mixed`
   - `local_citations`, `web_citations` (grouped)
   - `source_type` kept for backward compatibility

4. **UI**
   - Source badge (Local / Web / Mixed) with color
   - Documents section (local citations)
   - Web section (web citations with title, source, URL, snippet, Open link)
   - Updated empty-state copy for local + optional web

5. **Configuration**
   - `MESHMIND_WEB_RESEARCH_ENABLED` (default: false)
   - Structure in place for future Settings: enabled, allowed roles, use cases, citation requirement, auditability

### How Ask Decides Local vs Web vs Mixed

```
1. Run hybrid search (local docs).
2. local_strong = top chunk score ≥ 0.01
3. question_external = question contains keywords (current, today, latest, price, what is, etc.)
4. web_available = MESHMIND_WEB_RESEARCH_ENABLED

Routing:
- If local_strong → local only (no web)
- If !local_strong && question_external && web_available → web
- If !chunks && question && web_available → web
- If local_strong && question_external && web_available → mixed (both)
- If web attempted but fails → fallback to no-result message
- If !chunks && !web → no-result message
```

### Remaining Gaps Before Production

| Gap | Description |
|-----|-------------|
| **Settings UI** | No UI for enabling/disabling web research or policy. Controlled only via env. |
| **Allowed roles** | Code structured for it; not implemented. |
| **Auditability** | Web research usage not logged to audit events. |
| **Rate limiting** | No throttling for DuckDuckGo or fetch. |
| **Serper/API option** | DuckDuckGo only. Serper/Tavily would need API key and code path. |
| **Robots / ToS** | DuckDuckGo and target sites may restrict automated access. |
| **Caching** | Same query hits search/fetch every time; no cache. |

### Enabling Web Research

```bash
export MESHMIND_WEB_RESEARCH_ENABLED=true
# Then run query-api
```
