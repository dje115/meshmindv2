# MeshMind v2 — Enrichment Schema

## Output Structure

Enrichment adds structured metadata to chunks:

```json
{
  "language": "en",
  "document_class": "document",
  "summary": "...",
  "tags": ["tag1", "tag2"],
  "entities": [{"text": "Entity", "type": "PERSON"}],
  "sensitivity_hint": "internal"
}
```

## Fields

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| language | str \| null | langdetect | ISO 639-1 code |
| document_class | str | heuristic | document, spreadsheet, image |
| summary | str \| null | provider | LLM-generated summary |
| tags | list[str] | provider | Extracted tags |
| entities | list[dict] | provider | Named entities |
| sensitivity_hint | str \| null | provider | public, internal, confidential |

## Providers

- **Deterministic**: Language (langdetect), document_class (extension heuristic)
- **Pluggable**: Summary, tags, entities via `EnrichmentProvider`
