"""Local OCR engine using Tesseract (pytesseract)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytesseract
from PIL import Image

from .models import OcrPageResult, OcrResult

logger = logging.getLogger(__name__)

# Confidence threshold below which we mark as low_confidence
LOW_CONFIDENCE_THRESHOLD = 0.6


def _image_to_text_and_confidence(image: Image.Image) -> tuple[str, float]:
    """Run OCR on a PIL Image. Returns (text, mean_confidence)."""
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text_parts: list[str] = []
    confidences: list[float] = []
    num_blocks = len(data["text"])
    for i in range(num_blocks):
        t = (data["text"][i] or "").strip()
        if t:
            text_parts.append(t)
        c = float(data["conf"][i]) if data["conf"][i] != "-1" else 0.0
        if c > 0:
            confidences.append(c / 100.0)
    text = " ".join(text_parts)
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return text, mean_conf


def _run_ocr_on_image(path: Path, page_index: int = 0) -> OcrPageResult:
    """OCR a single image file."""
    img = Image.open(path).convert("RGB")
    text, conf = _run_ocr_on_pil(img, page_index)
    return OcrPageResult(
        page_index=page_index,
        text=text,
        confidence=conf,
        low_confidence=conf < LOW_CONFIDENCE_THRESHOLD,
        metadata={"source": str(path.name)},
    )


def _run_ocr_on_pil(img: Image.Image, page_index: int = 0) -> tuple[str, float]:
    """Run OCR on PIL Image. Returns (text, confidence)."""
    text, mean_conf = _image_to_text_and_confidence(img)
    return text, mean_conf


def ocr_image(path: Path, provenance: dict) -> OcrResult:
    """OCR a single image file (jpg, png, tiff, etc.)."""
    result = _run_ocr_on_image(path, 0)
    low_pages = [0] if result.low_confidence else []
    return OcrResult(
        full_text=result.text,
        pages=[result],
        provenance=provenance,
        extraction_metadata={
            "status": "success",
            "parser": "tesseract",
            "page_count": 1,
            "low_confidence_count": len(low_pages),
        },
        low_confidence_pages=low_pages,
    )


def ocr_pdf(path: Path, provenance: dict) -> OcrResult:
    """OCR a PDF by rendering pages to images and running Tesseract."""
    try:
        from pdf2image import convert_from_path
    except ImportError as e:
        raise RuntimeError(
            "pdf2image is required for PDF OCR. Install: pip install pdf2image. "
            "Also install poppler: apt install poppler-utils (Linux), brew install poppler (macOS)"
        ) from e

    images = convert_from_path(path, dpi=150)
    pages: list[OcrPageResult] = []
    low_pages: list[int] = []
    for i, img in enumerate(images):
        text, conf = _run_ocr_on_pil(img, i)
        low = conf < LOW_CONFIDENCE_THRESHOLD
        pages.append(
            OcrPageResult(
                page_index=i,
                text=text,
                confidence=conf,
                low_confidence=low,
                metadata={"page": i + 1},
            )
        )
        if low:
            low_pages.append(i)

    full_text = "\n\n".join(p.text for p in pages).strip()
    return OcrResult(
        full_text=full_text,
        pages=pages,
        provenance=provenance,
        extraction_metadata={
            "status": "success",
            "parser": "tesseract",
            "page_count": len(pages),
            "low_confidence_count": len(low_pages),
        },
        low_confidence_pages=low_pages,
    )
