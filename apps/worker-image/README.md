# MeshMind v2 — Image Worker

Processes image files: EXIF extraction, thumbnail generation, OCR, classification (screenshot/document-photo/photo), optional caption generation.

## Features

- **EXIF metadata**: Extracted via Pillow (where available)
- **Thumbnail**: Generated at 256×256 max, JPEG, base64 inline
- **OCR**: Local Tesseract for image text
- **Classification**: Heuristic detection of screenshot, document-photo, photo
- **Optional caption**: Pluggable `CaptionProvider` interface (no default implementation)

## Requirements

- Tesseract OCR: `apt install tesseract-ocr` (Linux), `brew install tesseract` (macOS)
- Python 3.11+, Pillow, pytesseract

## Running

```bash
pip install -e apps/worker-runtime -e apps/worker-image

export CONTROL_API_URL=http://localhost:3000
export MESHMIND_AGENT_NAME=meshmind-image
export MESHMIND_AGENT_CAPABILITIES=image

python apps/worker-image/main.py
```

## Testing

```bash
pip install -e "apps/worker-image[dev]"
cd apps/worker-image && pytest -v
```
