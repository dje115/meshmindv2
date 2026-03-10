"""EXIF parsing tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_image.exif import extract_exif


def test_exif_empty_image(tmp_path: Path) -> None:
    """Image with no EXIF returns empty dict."""
    p = tmp_path / "no_exif.png"
    img = Image.new("RGB", (10, 10), color="white")
    img.save(p)
    loaded = Image.open(p)
    exif = extract_exif(loaded)
    assert isinstance(exif, dict)
    # PNG typically has no EXIF; JPEG might have minimal
    assert "source_type" not in exif  # we don't add that


def test_exif_jpeg_may_have_data(tmp_path: Path) -> None:
    """JPEG may contain EXIF; extraction does not raise."""
    p = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    img.save(p, "JPEG")
    loaded = Image.open(p)
    exif = extract_exif(loaded)
    assert isinstance(exif, dict)
