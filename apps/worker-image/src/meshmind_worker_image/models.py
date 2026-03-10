"""Image processing output schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImageCategory(str, Enum):
    """Likely image category from heuristics."""

    PHOTO = "photo"
    SCREENSHOT = "screenshot"
    DOCUMENT_PHOTO = "document_photo"
    UNKNOWN = "unknown"


@dataclass
class ImageResult:
    """Searchable image document record."""

    provenance: dict[str, Any]
    exif: dict[str, Any]
    thumbnail_path: str | None  # Path or identifier for stored thumbnail
    thumbnail_base64: str | None  # Inline thumbnail (small)
    ocr_text: str
    ocr_confidence: float
    ocr_low_confidence: bool
    category: ImageCategory
    caption: str | None = None
    width: int = 0
    height: int = 0

    def to_artifacts(self) -> dict[str, Any]:
        """Convert to artifacts dict for complete() call."""
        return {
            "document": {
                "full_text": self.ocr_text,
                "pages": [
                    {
                        "page_index": 0,
                        "text": self.ocr_text,
                        "confidence": self.ocr_confidence,
                        "low_confidence": self.ocr_low_confidence,
                        "metadata": {"category": self.category.value},
                    }
                ],
                "provenance": self.provenance,
                "binary_assets": [],
                "image_metadata": {
                    "width": self.width,
                    "height": self.height,
                    "category": self.category.value,
                    "exif": self.exif,
                    "thumbnail_path": self.thumbnail_path,
                    "caption": self.caption,
                },
            },
            "extraction_metadata": {
                "status": "success",
                "confidence": self.ocr_confidence,
                "parser": "image",
                "category": self.category.value,
            },
            "downstream_enrich": True,
        }
