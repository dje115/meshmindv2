# Changelog

## [Unreleased]

### Fixed

- **Worker protocol**: Fixed 404 on progress/complete/fail endpoints — routes now use `:id` path param syntax (`/jobs/:id/complete` etc.).
- **Worker protocol**: Fixed 422 on register — added `#[serde(rename_all = "snake_case")]` to `WorkerCapability` so capabilities like `["filesystem", "docproc"]` deserialize correctly.
- **Worker protocol**: Fixed 500 on claim — changed `FOR UPDATE SKIP LOCKED` to `FOR UPDATE OF j SKIP LOCKED` to avoid Postgres error on nullable outer join.
- **Worker runtime**: Fixed `KeyError: "Attempt to overwrite 'name' in LogRecord"` — use `agent_name` instead of `name` in logging extra.

### Added

- **Reset stuck jobs**: `POST /api/jobs/reset-stuck` endpoint (auth required) to reset jobs stuck in `claimed` when a worker crashes.
- **Reset script**: `scripts/reset_stuck_jobs.py` for resetting stuck jobs via CLI.
