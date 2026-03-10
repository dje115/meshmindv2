"""EXIF metadata extraction via Pillow."""

from __future__ import annotations

from typing import Any

try:
    from PIL.ExifTags import TAGS
except ImportError:
    TAGS = {}


def extract_exif(image) -> dict[str, Any]:
    """Extract EXIF metadata from PIL Image. Returns sanitized dict."""
    exif: dict[str, Any] = {}
    try:
        exif_data = image.getexif()
        if not exif_data:
            return exif
        for tag_id, value in exif_data.items():
            if value is None:
                continue
            name = TAGS.get(tag_id, f"Tag_{tag_id}")
            # Serialize value (avoid raw bytes in JSON)
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8", errors="replace")
                except Exception:
                    value = "<binary>"
            exif[str(name)] = value
    except Exception:
        pass
    return exif
