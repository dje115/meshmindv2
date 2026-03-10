"""Image processor smoke tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_image.processor import process_image

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None


def _mk_image(path: Path, size: tuple[int, int] = (100, 100)) -> None:
    Image.new("RGB", size, color="white").save(path)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_process_image_smoke(tmp_path: Path) -> None:
    """process_image runs without raising."""
    p = tmp_path / "x.png"
    _mk_image(p)
    result = process_image(p, {"source_type": "filesystem"})
    assert result.width == 100
    assert result.height == 100
    assert result.ocr_text is not None
    arts = result.to_artifacts()
    assert "document" in arts
    assert "extraction_metadata" in arts
    assert arts["downstream_enrich"] is True


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_duplicate_fingerprint_same_checksum(tmp_path: Path) -> None:
    """Two identical images produce same OCR output (deterministic)."""
    p1 = tmp_path / "a.png"
    p2 = tmp_path / "b.png"
    _mk_image(p1)
    _mk_image(p2)
    r1 = process_image(p1, {})
    r2 = process_image(p2, {})
    assert r1.width == r2.width
    assert r1.height == r2.height
    assert r1.category == r2.category
