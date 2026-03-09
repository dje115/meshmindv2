# ADR-001: Server-First Architecture

## Status

Accepted.

## Context

MeshMind v1 was local-first with peer-to-peer mesh. v2 targets on-prem deployments where a central server is the source of truth, and clients (browser, workers) interact via HTTP.

## Decision

- **Server-first:** The Core service owns all state and business logic.
- **Browser-first:** The UI is a React SPA that consumes the Core HTTP API; no desktop app.
- **Stateless clients:** Workers and UI do not hold durable state; Core is the single source of truth.

## Consequences

- Simpler deployment: one Core process (or replicated behind load balancer).
- No peer discovery, gossip, or mTLS mesh.
- Workers are job executors; they claim work from Core and POST results.
- UI requires network access to Core; no offline mode in v2.

## References

- PRODUCT_SCOPE.md (non-goals: peer mesh, offline-first)
- ARCHITECTURE.md
- SERVICE_BOUNDARIES.md
