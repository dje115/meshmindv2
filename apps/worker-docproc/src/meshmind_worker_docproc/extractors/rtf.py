"""RTF extraction using striprtf."""

from __future__ import annotations

from pathlib import Path

from striprtf.striprtf import rtf_to_text

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    PageBlock,
)
from .base import ExtractionResult


def extract_rtf(path: Path, provenance: dict) -> ExtractionResult:
    """Extract RTF to plain text. Single logical page."""
    try:
        raw = path.read_bytes()
        content = rtf_to_text(raw.decode("utf-8", errors="replace"))
    except Exception as e:
        return ExtractionResult(failure_reason=f"rtf read error: {e}")

    text = content.strip()
    doc = NormalizedDocument(
        full_text=text,
        pages=[PageBlock(page_index=0, text=text)],
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.9,
            page_count=1,
            parser="striprtf",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)
