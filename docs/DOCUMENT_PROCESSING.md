# MeshMind v2 — Document Processing Worker

## Overview

The document processing worker (`apps/worker-docproc`) extracts normalized text and structure from document-like source items. It supports PDF, Word, Excel, plain text, HTML, RTF, CSV, and JSON.

## Supported File Types

| Extension | Parser | Notes |
|-----------|--------|-------|
| PDF | pypdf | Page-aware; OCR fallback when native text is sparse |
| DOCX | python-docx | Full support |
| DOC | Apache Tika | Legacy Word; requires Tika server |
| XLSX | openpyxl | Sheet-aware; values only |
| XLS | xlrd, then Tika | xlrd first; Tika fallback on failure |
| TXT, MD | stdlib | Plain text |
| RTF | striprtf | Plain text extraction |
| HTML | beautifulsoup4 | Script/style removed |
| CSV, JSON | stdlib | Structured text summaries |

## Apache Tika (Legacy Office)

`.doc` and problematic `.xls` files use Apache Tika via HTTP. A Tika server must be running.

| Env Var | Default | Description |
|---------|---------|-------------|
| `TIKA_SERVER_ENDPOINT` | `http://localhost:9998` | Tika server base URL |
| `TIKA_TIMEOUT_SECS` | `60` | Request timeout |

**Start Tika (Docker):**
```bash
docker run -d -p 9998:9998 apache/tika:latest
```

**Or run JAR:**
```bash
java -jar tika-server-2.x.x.jar
```

When Tika is unavailable or parsing fails, a structured failure is returned.

## Running the Worker

```bash
pip install -e apps/worker-runtime -e apps/worker-docproc

export CONTROL_API_URL=http://localhost:3000
export MESHMIND_AGENT_NAME=meshmind-docproc
export MESHMIND_AGENT_CAPABILITIES=docproc
export TIKA_SERVER_ENDPOINT=http://localhost:9998  # for .doc and .xls fallback

python apps/worker-docproc/main.py
```

## Testing

```bash
pip install -e "apps/worker-docproc[dev]"
cd apps/worker-docproc && python -m pytest -v
```

Optional integration tests with real-world Office files: set `MESHTEST_PATH` to a folder containing `.doc`/`.xls` samples; tests skip if unset.

## Output Schema

Extraction produces a normalized document with `full_text`, `pages`, `sheets`, `provenance`, and `extraction_metadata`. See [apps/worker-docproc/README.md](../apps/worker-docproc/README.md) for full schema.
