"""OCR output schema: text, confidence, per-page metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OcrPageResult:
    """Per-page or per-image OCR result."""

    page_index: int
    text: str
    confidence: float  # 0.0–1.0
    low_confidence: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OcrResult:
    """Complete OCR result with provenance."""

    full_text: str
    pages: list[OcrPageResult]
    provenance: dict[str, Any]
    extraction_metadata: dict[str, Any]
    low_confidence_pages: list[int] = field(default_factory=list)

    def to_artifacts(self) -> dict[str, Any]:
        """Convert to artifacts dict for complete() call."""
        return {
            "document": {
                "full_text": self.full_text,
                "pages": [
                    {
                        "page_index": p.page_index,
                        "text": p.text,
                        "confidence": p.confidence,
                        "low_confidence": p.low_confidence,
                        "metadata": p.metadata,
                    }
                    for p in self.pages
                ],
                "provenance": self.provenance,
            },
            "ocr_metadata": {
                **self.extraction_metadata,
                "low_confidence_pages": self.low_confidence_pages,
            },
            "downstream_enrich": True,
        }
