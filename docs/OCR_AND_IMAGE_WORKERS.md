# MeshMind v2 — OCR and Image Workers

## OCR Worker (`apps/worker-ocr`)

### OCR Engine Choice: Tesseract (pytesseract)

**Why Tesseract:**
- **Local only** — No cloud APIs; meets the requirement for no cloud OCR
- **CPU-based** — Runs on standard hardware without GPU
- **Mature** — Widely used, well-documented
- **Python bindings** — pytesseract is stable and simple
- **Multiple languages** — Supports 100+ languages

**Alternatives considered:**
- EasyOCR, PaddleOCR: More accurate in some cases but heavier dependencies
- Cloud (Google Vision, AWS Textract): Explicitly excluded

### Page Preprocessing

- PDF: Rendered via `pdf2image` (Poppler) at 150 DPI
- Images: Loaded with Pillow, converted to RGB
- No deskew/denoise in initial implementation; can be added as preprocessing steps

### Output

- `full_text`: Concatenated per-page text
- `pages[]`: Per-page `text`, `confidence`, `low_confidence`, `metadata`
- `low_confidence_pages`: Indices of pages below threshold (0.6)
- Provenance passed through from source_item

### Provenance and Source Location

- `source_item.provenance` from the job is passed to the OCR engine
- Output `document.provenance` contains the same `absolute_path`, `filename`, `extension`, etc.
- All outputs are linked to the source item via job `source_item_id`; control plane stores artifacts with job/source references

### Current Limitations

- PDF requires Poppler (pdf2image); not all environments have it
- No deskew or advanced preprocessing for poor scans
- Single-language default (Tesseract `eng`); language config can be added
- CPU-only; slower on large multi-page PDFs

### Performance Expectations (CPU)

- **Single image (1MP)**: ~0.5–2 s
- **PDF (10 pages, 150 DPI)**: ~5–20 s
- **Large scanned PDF (50+ pages)**: 1–3 min

---

## Image Worker (`apps/worker-image`)

### Image Classification Approach

Heuristic rules (no ML model):

| Category           | Criteria                                                         |
|--------------------|------------------------------------------------------------------|
| **screenshot**     | Resolution in common screen sizes (1920×1080, 1366×768, etc.)    |
| **document_photo** | Substantial OCR text (>50 chars) and confidence ≥ 0.3            |
| **photo**          | Default for other images                                         |
| **unknown**        | Zero width/height                                                |

Classification can be extended later with a local model (e.g. CLIP) via the caption interface.

### Optional Caption

- `CaptionProvider` abstract interface: `caption(image_path, metadata) -> str | None`
- No default implementation; can be wired to Ollama, CLIP, etc. later
- Extensible without over-engineering

### Output

- EXIF: Sanitized dict (no raw bytes)
- Thumbnail: JPEG, max 256×256, base64 inline
- OCR text, confidence, low_confidence
- Category, dimensions
- Provenance preserved

### Provenance

- Same pattern as OCR: `provenance` from source_item flows through to `document.provenance` in artifacts
- All outputs reference the same source_item

---

## How Images Become Searchable

1. **Connector** discovers image files, creates source_items, dispatches `image` jobs
2. **Image worker** runs: EXIF, thumbnail, OCR, classification
3. **Artifacts** include `document.full_text` (OCR) and `image_metadata`
4. **Chunking/enrichment phase** (downstream): `full_text` is chunked and indexed; embeddings generated
5. Search runs over chunk text and metadata; thumbnails/captions can be stored for display

---

## How Low-Confidence OCR Is Surfaced in the UI Later

- `ocr_metadata.low_confidence_pages`: List of page indices
- Per-page `low_confidence: true` in `pages[]`
- UI can:
  - Show a badge or icon for “OCR may be inaccurate”
  - Offer “Review OCR” for low-confidence pages
  - Filter search to exclude low-confidence content (optional)
  - Display confidence in source/item detail views

---

## Follow-On Adjustments Before Chunking/Enrichment Phase

1. **Job flow**: Ensure control plane creates `ocr` jobs for PDFs with `needs_ocr` (docproc already does this)
2. **Job flow**: Ensure connector creates `image` jobs for image extensions (already done)
3. **Artifact schema**: Align `document` / `ocr_metadata` / `image_metadata` with chunking input schema
4. **Thumbnail storage**: Decide where thumbnails live (disk path vs. object store) and how chunks reference them
5. **Optional**: Add `language` config for Tesseract
6. **Optional**: Add preprocessing (deskew, denoise) for poor scans
