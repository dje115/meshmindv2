# MeshMind v2 — API Conventions

## JSON API Only

All endpoints consume and return JSON.

## Error Model

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "user not found"
  },
  "request_id": "uuid-optional"
}
```

| Code | HTTP Status |
|------|-------------|
| UNAUTHORIZED | 401 |
| FORBIDDEN | 403 |
| NOT_FOUND | 404 |
| CONFLICT | 409 |
| BAD_REQUEST | 400 |
| INTERNAL_ERROR | 500 |

## Request ID

- Header: `x-request-id` (optional; generated if absent)
- Response header: `x-request-id`
- Included in error body when available

## Authentication

- `Authorization: Bearer <token>` for protected routes

## Base Path

- API: `/api/*`
- Swagger UI: `/swagger-ui`
- Health: `/health`, `/ready` (root); `/api/health`, `/api/ready`
