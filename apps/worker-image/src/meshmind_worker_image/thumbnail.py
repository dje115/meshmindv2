"""Thumbnail generation."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

MAX_THUMBNAIL_SIZE = (256, 256)


def generate_thumbnail(path: Path, output_path: Path | None = None) -> tuple[str | None, str | None]:
    """Generate thumbnail. Returns (output_path_or_none, base64_inline_or_none).

    If output_path is given, saves thumbnail there and returns it.
    Always returns base64-encoded inline thumbnail for embedding.
    """
    img = Image.open(path).convert("RGB")
    img.thumbnail(MAX_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=85)
        return str(output_path), b64
    return None, b64
