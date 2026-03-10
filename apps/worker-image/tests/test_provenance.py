"""Provenance preservation tests for image worker."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_image.processor import process_image

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None


def _mk_image(path: Path) -> None:
    Image.new("RGB", (50, 50), color="white").save(path)


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
def test_provenance_in_output(tmp_path: Path) -> None:
    """Provenance is preserved in image processing output."""
    p = tmp_path / "photo.jpg"
    _mk_image(p)
    prov = {
        "source_type": "filesystem",
        "absolute_path": "/data/photos/photo.jpg",
        "filename": "photo.jpg",
    }
    result = process_image(p, prov)
    arts = result.to_artifacts()
    assert arts["document"]["provenance"]["absolute_path"] == "/data/photos/photo.jpg"
