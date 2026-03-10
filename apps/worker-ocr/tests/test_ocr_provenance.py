"""Provenance preservation tests for OCR worker."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_ocr.ocr_engine import ocr_image

import shutil
TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
from meshmind_worker_ocr.models import OcrResult


def _mk_image(path: Path) -> None:
    Image.new("RGB", (50, 50), color="white").save(path)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_provenance_passed_through(tmp_path: Path) -> None:
    """Source provenance is preserved in OCR output."""
    p = tmp_path / "doc.png"
    _mk_image(p)
    prov = {
        "source_type": "filesystem",
        "absolute_path": "/data/docs/doc.png",
        "relative_path": "docs/doc.png",
        "filename": "doc.png",
        "extension": "png",
    }
    result = ocr_image(p, prov)
    arts = result.to_artifacts()
    assert arts["document"]["provenance"]["absolute_path"] == "/data/docs/doc.png"
    assert arts["document"]["provenance"]["filename"] == "doc.png"
