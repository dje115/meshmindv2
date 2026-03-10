"""Low-confidence OCR handling tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_ocr.ocr_engine import ocr_image

import shutil

try:
    from pytesseract import TesseractNotFoundError
except ImportError:
    TesseractNotFoundError = Exception  # type: ignore

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
PROVENANCE = {"source_type": "filesystem", "absolute_path": "/tmp/x.png"}


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_low_confidence_flagged(tmp_path: Path) -> None:
    """Blank/simple images produce low_confidence flag."""
    p = tmp_path / "blank.png"
    Image.new("RGB", (100, 100), color="white").save(p)
    try:
        result = ocr_image(p, PROVENANCE)
    except TesseractNotFoundError:
        pytest.skip("Tesseract not installed or not in PATH")
    assert len(result.pages) == 1
    assert result.pages[0].low_confidence or result.pages[0].confidence < 0.7


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_low_confidence_in_artifacts(tmp_path: Path) -> None:
    """low_confidence_pages appears in artifacts."""
    p = tmp_path / "blank.png"
    Image.new("RGB", (50, 50), color="white").save(p)
    result = ocr_image(p, PROVENANCE)
    arts = result.to_artifacts()
    assert "low_confidence_pages" in arts["ocr_metadata"]
