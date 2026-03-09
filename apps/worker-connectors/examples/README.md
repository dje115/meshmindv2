# Filesystem Connector Examples

## Example config

Use `filesystem-config.example.json` as a template for source config when creating a filesystem source via the control plane API.

## Minimal source creation

```bash
# Create a filesystem source (requires auth)
curl -X POST http://localhost:3000/api/sources \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "YOUR_WORKSPACE_ID",
    "name": "My Docs",
    "kind": "filesystem",
    "config": {
      "path": "/path/to/scan",
      "exclude_patterns": ["**/node_modules/**"]
    }
  }'
```

## Trigger ingest (creates scan job)

The control plane needs an ingest trigger endpoint. Once available:

```bash
curl -X POST http://localhost:3000/api/sources/SOURCE_ID/ingest \
  -H "Authorization: Bearer YOUR_JWT"
```

The filesystem connector will claim the resulting job and run the scan.
