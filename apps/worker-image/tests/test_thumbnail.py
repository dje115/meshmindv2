"""Thumbnail generation tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from meshmind_worker_image.thumbnail import generate_thumbnail


def test_thumbnail_generates_base64(tmp_path: Path) -> None:
    """Thumbnail returns base64 inline."""
    p = tmp_path / "large.png"
    img = Image.new("RGB", (500, 500), color="blue")
    img.save(p)
    saved, b64 = generate_thumbnail(p, None)
    assert saved is None
    assert b64 is not None
    assert len(b64) > 0
    import base64
    decoded = base64.b64decode(b64)
    assert len(decoded) > 0


def test_thumbnail_saves_to_path(tmp_path: Path) -> None:
    """Thumbnail can be saved to output path."""
    p = tmp_path / "in.png"
    out = tmp_path / "thumb" / "out.jpg"
    img = Image.new("RGB", (300, 300), color="red")
    img.save(p)
    saved, b64 = generate_thumbnail(p, out)
    assert saved == str(out)
    assert out.exists()
    loaded = Image.open(out)
    assert loaded.size[0] <= 256 and loaded.size[1] <= 256
