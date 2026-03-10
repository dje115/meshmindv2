"""OCR engine tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_ocr.ocr_engine import ocr_image, ocr_pdf

import shutil
TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
from meshmind_worker_ocr.models import OcrResult

PROVENANCE = {"source_type": "filesystem", "absolute_path": "/tmp/sample.png", "extension": "png"}


def _create_text_image(path: Path, text: str = "Hello OCR test") -> None:
    """Create a minimal image with text (PIL). Tesseract may or may not read it."""
    img = Image.new("RGB", (200, 50), color="white")
    # Pillow doesn't draw text easily without ImageDraw/font - create simple pattern
    pixels = img.load()
    for y in range(10, 40):
        for x in range(20, 180):
            pixels[x, y] = (0, 0, 0) if (x + y) % 4 == 0 else (255, 255, 255)
    img.save(path)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_ocr_image_smoke(tmp_path: Path) -> None:
    """OCR runs on image without raising."""
    p = tmp_path / "sample.png"
    _create_text_image(p)
    result = ocr_image(p, PROVENANCE)
    assert isinstance(result, OcrResult)
    assert result.full_text is not None
    assert len(result.pages) == 1
    assert result.pages[0].page_index == 0
    assert result.provenance == PROVENANCE
    assert "tesseract" in result.extraction_metadata.get("parser", "")


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_ocr_image_low_confidence() -> None:
    """Blank/simple image yields low confidence."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        p = Path(f.name)
    try:
        img = Image.new("RGB", (100, 100), color="white")
        img.save(p)
        result = ocr_image(p, PROVENANCE)
        assert result.pages[0].low_confidence or result.pages[0].confidence < 0.7
    finally:
        p.unlink(missing_ok=True)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_ocr_image_provenance_preserved(tmp_path: Path) -> None:
    """Provenance is passed through to output."""
    p = tmp_path / "x.png"
    _create_text_image(p)
    prov = {"source_type": "filesystem", "absolute_path": str(p), "filename": "x.png"}
    result = ocr_image(p, prov)
    assert result.provenance == prov
    arts = result.to_artifacts()
    assert arts["document"]["provenance"] == prov


def test_ocr_pdf_minimal() -> None:
    """ocr_pdf either runs or raises if pdf2image/poppler unavailable."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 minimal")
        p = Path(f.name)
    try:
        try:
            result = ocr_pdf(p, PROVENANCE)
            assert isinstance(result, OcrResult)
        except Exception as e:
            # RuntimeError (ocr_engine), PDFInfoNotInstalledError (poppler missing)
            err = str(e).lower()
            assert "pdf2image" in err or "poppler" in err or "pdfinfo" in err or "unable" in err
    finally:
        p.unlink(missing_ok=True)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_to_artifacts_structure(tmp_path: Path) -> None:
    """to_artifacts returns expected schema."""
    p = tmp_path / "sample.png"
    _create_text_image(p)
    result = ocr_image(p, PROVENANCE)
    arts = result.to_artifacts()
    assert "document" in arts
    assert "full_text" in arts["document"]
    assert "pages" in arts["document"]
    assert "provenance" in arts["document"]
    assert "ocr_metadata" in arts
    assert "low_confidence_pages" in arts["ocr_metadata"]
    assert arts["downstream_enrich"] is True
