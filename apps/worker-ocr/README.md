# MeshMind v2 — OCR Worker

Local OCR for scanned PDFs and image files using Tesseract.

## Features

- Scanned PDFs and images (jpg, png, tiff, etc.)
- Local OCR only (no cloud)
- Per-page text, confidence, metadata
- Low-confidence marking for review
- Provenance preserved through pipeline

## Requirements

- **Tesseract OCR**: `apt install tesseract-ocr` (Linux), `brew install tesseract` (macOS)
- **Poppler** (for PDF): `apt install poppler-utils` (Linux), `brew install poppler` (macOS)

## Running

```bash
pip install -e apps/worker-runtime -e apps/worker-ocr

export CONTROL_API_URL=http://localhost:3000
export MESHMIND_AGENT_NAME=meshmind-ocr
export MESHMIND_AGENT_CAPABILITIES=ocr

python apps/worker-ocr/main.py
```

## Testing

```bash
pip install -e "apps/worker-ocr[dev]"
cd apps/worker-ocr && pytest -v
```
