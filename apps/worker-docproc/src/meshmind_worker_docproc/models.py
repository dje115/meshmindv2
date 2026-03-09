"""Output schema and extraction metadata models for docproc worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExtractionStatus(str, Enum):
    """Outcome of extraction attempt."""

    SUCCESS = "success"
    NEEDS_OCR = "needs_ocr"
    FAILED = "failed"


@dataclass
class PageBlock:
    """Page-aware content block."""

    page_index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SheetBlock:
    """Sheet-aware content block for spreadsheets."""

    sheet_index: int
    sheet_name: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process."""

    status: ExtractionStatus
    confidence: float  # 0.0–1.0
    page_count: int | None = None
    sheet_count: int | None = None
    parser: str = ""
    message: str | None = None
    failure_reason: str | None = None


@dataclass
class NormalizedDocument:
    """Normalized document record output."""

    full_text: str
    pages: list[PageBlock] = field(default_factory=list)
    sheets: list[SheetBlock] = field(default_factory=list)
    extraction_metadata: ExtractionMetadata = field(default_factory=lambda: ExtractionMetadata(ExtractionStatus.SUCCESS, 1.0))
    provenance: dict[str, Any] = field(default_factory=dict)
    binary_assets: list[dict[str, Any]] = field(default_factory=list)

    def to_artifacts(self) -> dict[str, Any]:
        """Convert to artifacts dict for complete() call."""
        return {
            "document": {
                "full_text": self.full_text,
                "pages": [
                    {"page_index": p.page_index, "text": p.text, "metadata": p.metadata}
                    for p in self.pages
                ],
                "sheets": [
                    {
                        "sheet_index": s.sheet_index,
                        "sheet_name": s.sheet_name,
                        "text": s.text,
                        "metadata": s.metadata,
                    }
                    for s in self.sheets
                ],
                "provenance": self.provenance,
                "binary_assets": self.binary_assets,
            },
            "extraction_metadata": {
                "status": self.extraction_metadata.status.value,
                "confidence": self.extraction_metadata.confidence,
                "page_count": self.extraction_metadata.page_count,
                "sheet_count": self.extraction_metadata.sheet_count,
                "parser": self.extraction_metadata.parser,
                "message": self.extraction_metadata.message,
                "failure_reason": self.extraction_metadata.failure_reason,
            },
            "downstream_ocr": self.extraction_metadata.status == ExtractionStatus.NEEDS_OCR,
            "downstream_enrich": self.extraction_metadata.status == ExtractionStatus.SUCCESS,
        }
