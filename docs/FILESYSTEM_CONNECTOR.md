# MeshMind v2 — Filesystem Connector

## Overview

The filesystem connector discovers files under configured folders, fingerprints them, captures provenance metadata, and dispatches downstream jobs for document processing or image handling. It does **not** perform document extraction, OCR, or LLM enrichment.

## Configuring a Filesystem Source

### Source config schema

When creating a filesystem source via `POST /api/sources`, use:

```json
{
  "workspace_id": "...",
  "name": "My Docs",
  "kind": "filesystem",
  "config": {
    "path": "/absolute/path/to/scan",
    "include_patterns": ["**/*.pdf", "**/*.docx"],
    "exclude_patterns": ["**/node_modules/**", "**/.git/**"],
    "max_depth": -1,
    "batch_size": 100,
    "rate_limit_delay_secs": 0.1
  }
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| path | Yes | — | Root path to scan (absolute or resolved) |
| include_patterns | No | [] | Glob patterns for files to include. If empty, all supported extensions under path are included. |
| exclude_patterns | No | node_modules, .git | Glob patterns to exclude |
| max_depth | No | -1 | Max recursion depth (0 = path only, -1 = unlimited) |
| batch_size | No | 100 | Max items per batch when submitting to control plane |
| rate_limit_delay_secs | No | 0.1 | Delay between batches |

### Supported file extensions

| Class | Extensions |
|-------|------------|
| Documents | pdf, docx, doc, xlsx, xls, txt, md, rtf, html, csv, json |
| Images | jpg, jpeg, png, tiff |

## Running the Connector

1. Install dependencies:
   ```bash
   cd apps/worker-runtime && pip install -e .
   cd ../worker-connectors && pip install -e .
   ```

2. Set environment variables:
   - `CONTROL_API_URL` — Control plane URL (default: http://localhost:3000)
   - `MESHMIND_AGENT_NAME` — Agent name (default: meshmind-worker)
   - `MESHMIND_AGENT_CAPABILITIES` — Comma-separated, e.g. `filesystem,docproc`
   - `MESHMIND_CHANGE_STORE` — Path for change-detection state (default: data/connector-state/{source_id}.json)

3. Run:
   ```bash
   python apps/worker-connectors/main.py
   # or: python -m meshmind_connectors.cli
   # or: meshmind-fs-connector (if on PATH)
   ```

## Re-scan / Reindex

- **Change store**: The connector persists a JSON file per source (`data/connector-state/{source_id}.json`) with fingerprints and paths. On each scan, it compares current files to this store.
- **New**: Files not in the store are submitted as source items and jobs are dispatched.
- **Modified**: Files with same path but changed mtime/size get a new fingerprint and are re-submitted.
- **Deleted**: Fingerprints no longer present on disk are pruned from the store. The control plane does not automatically delete source items for deleted files; that is handled by a separate cleanup process if desired.
- **Re-scan**: Trigger a new scan by creating a new job for the source (e.g. `POST /api/sources/:id/ingest`). The connector claims it and runs a full scan. Unchanged files are skipped; new/modified are processed.
- **Stuck jobs**: If a connector crashes after claiming a job, the job stays `claimed`. Use `POST /api/jobs/reset-stuck` or `python scripts/reset_stuck_jobs.py` to reset it to `queued`.

## Provenance and Source Location

Every discovered item stores provenance metadata so MeshMind can answer:
- Where did this come from?
- Which file or system did this data come from?
- What original location should be opened or referenced?

### Captured fields

| Field | Description |
|-------|-------------|
| source_type | `filesystem` |
| source_root | Absolute root path of the scan |
| absolute_path | Full path to the file |
| relative_path | Path relative to source_root |
| filename | Base name |
| extension | Lowercase extension |
| file_size_bytes | Size in bytes |
| created_time_iso | Creation time (ISO 8601) if available |
| modified_time_iso | Modification time (ISO 8601) |
| discovery_fingerprint | Scan fingerprint (path+mtime+size hash) for change detection |
| local_path | Same as absolute_path, normalized |
| hostname | Machine hostname |
| agent_identity | Connector/agent identifier |
| open_target | `file://` URL or UNC path for opening the file |

### open_target

- Local paths: `file:///C:/docs/file.pdf` or `file:///home/user/docs/file.pdf`
- UNC paths: `file:////server/share/file.pdf`

## Connector Flow (Step by Step)

1. **Register** — Connector registers with control plane as agent with capabilities `filesystem`, `docproc`.
2. **Heartbeat** — Sends heartbeat every 30s (configurable).
3. **Claim** — Polls for jobs; claims a filesystem scan job when available.
4. **Load config** — Reads `path`, `include_patterns`, `exclude_patterns`, etc. from job config.
5. **Scan** — Recursively discovers files under `path`, filters by extensions and patterns.
6. **Change detection** — Compares to local change store; classifies as new, modified, or unchanged.
7. **Prune deleted** — Removes fingerprints for files no longer on disk from the store.
8. **Submit items** — Batches new/modified files; calls `POST /api/workers/sources/:source_id/items` with fingerprint and provenance.
9. **Dispatch jobs** — For each created source item, calls `POST /api/workers/jobs` with `job_kind` = `docproc` (documents) or `image` (images).
10. **Complete** — Marks the scan job complete.
11. **Loop** — Returns to claim.

## Cross-Platform Caveats

- **Path separators**: Paths are normalized to forward slashes in provenance for consistency.
- **UNC paths**: On Windows, `\\\\server\\share` is supported; `open_target` uses `file://`-style encoding (e.g. `file:////server/share/file.pdf`).
- **Symlinks**: The connector follows `Path.rglob`; symlinks to directories may be followed depending on the OS. Consider excluding them via `exclude_patterns` if needed.
- **Case sensitivity**: Extensions are matched case-insensitively. On case-sensitive filesystems (e.g. Linux), `File.PDF` and `file.pdf` are treated the same.
- **Locked files**: Files that cannot be stat'd (e.g. permission denied) are skipped; no retry is performed.
- **Change store location**: Put the change store outside the scan path to avoid scanning `state.json`.

## Provenance Metadata Captured

Every discovered item includes at least:

| Field | Example |
|-------|---------|
| source_type | `filesystem` |
| source_root | `C:/data/docs` or `/home/user/docs` |
| absolute_path | `C:/data/docs/sub/file.pdf` |
| relative_path | `sub/file.pdf` |
| filename | `file.pdf` |
| extension | `pdf` |
| file_size_bytes | `1024` |
| created_time_iso | `2025-03-09T12:00:00+00:00` |
| modified_time_iso | `2025-03-09T12:00:00+00:00` |
| discovery_fingerprint | SHA256 of `path\|mtime\|size` (scan/change detection only) |
| local_path | Same as absolute_path |
| hostname | `DESKTOP-ABC` |
| agent_identity | `filesystem-connector:550e8400` |
| open_target | `file:///C:/data/docs/sub/file.pdf` |

> **Note:** A true content checksum (hash of file bytes) may be added during document processing or a later phase for content identity and deduplication. The `discovery_fingerprint` is used only for scan/change detection.
