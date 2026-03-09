# MeshMind v2 – Document Processing Worker

Extracts normalized text and structure from document-like source items. Supports PDF (with readable vs OCR detection), DOCX, XLSX, TXT, MD, RTF, HTML, CSV, JSON, and limited DOC/XLS.

## Supported File Types

| Extension | Parser | Page/Sheet Aware | Notes |
|-----------|--------|------------------|-------|
| PDF | pypdf | Yes (page) | Native text extraction; OCR fallback when text is sparse |
| DOCX | python-docx | No | Full support |
| DOC | Apache Tika | No | Primary path; requires Tika server (TIKA_SERVER_ENDPOINT) |
| XLSX | openpyxl | Yes (sheet) | Values only; formulas evaluated |
| XLS | xlrd, then Tika | Yes (sheet) | xlrd first; Tika fallback on failure |
| TXT | stdlib | No | UTF-8, errors replaced |
| MD | stdlib | No | Preserved as-is |
| RTF | striprtf | No | Plain text extraction |
| HTML | beautifulsoup4 | No | Script/style removed |
| CSV | stdlib | No | Tabular summary |
| JSON | stdlib | No | Structured text summary (keys + values) |

## Apache Tika (Legacy Office)

DOC and XLS (when xlrd fails) use Apache Tika via HTTP. A Tika server must be running.

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

## Extraction Limitations

- **DOC (legacy Word)**: Uses Apache Tika. Requires Tika server. Returns structured failure when Tika is unreachable or file is corrupt/encrypted.
- **XLS/XLSX**: Formulas become evaluated values. Complex formatting, macros, and embedded objects are not captured. XLS falls back to Tika when xlrd fails.
- **PDF**: No OCR performed here. When native text is poor, status is `needs_ocr` and a downstream OCR job is dispatched.
- **HTML**: Inline scripts/styles removed; structure simplified for retrieval.

## OCR Fallback Trigger

A PDF is treated as **needs OCR** when:

1. Total extracted text is below 100 characters, or  
2. Average characters per page is below 50, or  
3. Meaningful word count is below 10.

In that case:

- `extraction_metadata.status` = `"needs_ocr"`
- `downstream_ocr` = `true`
- The worker creates a downstream OCR job via `create_job(source_id, source_item_id, "ocr")`.

Page references are preserved: `pages[i].page_index` and `pages[i].metadata.needs_ocr` for OCR routing.

## Provenance and Source Location

Provenance from `source_item.provenance` is passed into the extractor and attached to the output:

- `document.provenance` contains the original provenance (e.g. `source_type`, `absolute_path`, `relative_path`, `filename`, `extension`, `open_target`).
- The worker resolves the file path from `absolute_path`, `local_path`, or `open_target` (file:// URL).
- All extracted content carries this provenance; no content is silently detached from its source.

## Output Schema

### Normalized Document

```json
{
  "document": {
    "full_text": "...",
    "pages": [{"page_index": 0, "text": "...", "metadata": {}}],
    "sheets": [{"sheet_index": 0, "sheet_name": "Sheet1", "text": "...", "metadata": {}}],
    "provenance": { "source_type": "filesystem", "absolute_path": "...", ... },
    "binary_assets": []
  },
  "extraction_metadata": {
    "status": "success",
    "confidence": 0.95,
    "page_count": 1,
    "parser": "pypdf",
    "message": null,
    "failure_reason": null
  },
  "downstream_ocr": false,
  "downstream_enrich": true
}
```

### Extraction Status

- `success` – Extraction succeeded; ready for enrichment/chunking.
- `needs_ocr` – Native text insufficient; OCR job dispatched.
- `failed` – Extraction failed; see `failure_reason`.

## Extracted Output Schema Summary

| Field | Type | Description |
|-------|------|-------------|
| `document.full_text` | string | Concatenated normalized text |
| `document.pages` | array | Page blocks with `page_index`, `text`, `metadata` |
| `document.sheets` | array | Sheet blocks with `sheet_index`, `sheet_name`, `text` |
| `document.provenance` | object | Original source provenance |
| `extraction_metadata.status` | enum | `success`, `needs_ocr`, `failed` |
| `extraction_metadata.confidence` | float | 0.0–1.0 |
| `downstream_ocr` | bool | True when OCR job should be created |
| `downstream_enrich` | bool | True when ready for chunking |

## How Failures Are Surfaced

- **Extractor failure**: Returns `ExtractionResult(failure_reason="...")`. Processor raises, worker calls `client.fail()` with the error string.
- **Control plane**: Records error in `jobs.error` and `job_runs.error`, logs in `job_logs`. Retries with backoff (configurable).
- **Structured failure**: DOC/unsupported types return `failure_reason` in the result; never silently dropped.

## How PDF Readable vs OCR Is Decided

1. Extract text per page with pypdf.
2. Compute: total chars, avg chars/page, meaningful word count.
3. If total < 100 chars **or** avg < 50 chars/page **or** words < 10 → `needs_ocr`.
4. Otherwise → `success`.

## Failure Handling

Failures are **never silently dropped**:

- Parse/read errors return `ExtractionResult(failure_reason="...")`.
- The worker calls `client.fail(job_id, job_run_id, error)` with a structured message.
- Retries are managed by the control plane (exponential backoff).
- `failure_reason` is included in extraction metadata when applicable.

## LLM Usage

- **Deterministic extraction only** – Parsers (pypdf, python-docx, etc.) are used for extraction.
- LLM support may be used for **optional** cleanup or classification (e.g. summarization, tagging) but **not** as a substitute for deterministic text extraction.
- Current implementation uses no LLM calls.

## Running the Worker

```bash
# Install
pip install -e apps/worker-runtime -e apps/worker-docproc

# Environment
export CONTROL_API_URL=http://localhost:3000
export MESHMIND_AGENT_NAME=meshmind-docproc
export MESHMIND_AGENT_CAPABILITIES=docproc
# For .doc and .xls fallback:
export TIKA_SERVER_ENDPOINT=http://localhost:9998

# Run
python apps/worker-docproc/main.py
```

## Testing

```bash
pip install -e "apps/worker-docproc[dev]"
cd apps/worker-docproc && pytest -v
```

Tests cover:

- Fixture-based integration (TXT, MD, CSV, JSON)
- PDF readable vs needs-OCR detection
- Malformed files (e.g. invalid JSON)
- Provenance preservation
- Artifacts schema
- DOC (Tika primary; structured failure when Tika down)
- XLS xlrd + Tika fallback
- Optional real-world integration tests (Meshtest/Test1)
