"""Plain text and Markdown extraction."""

from __future__ import annotations

from pathlib import Path

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    PageBlock,
)
from .base import ExtractionResult


def extract_txt(path: Path, provenance: dict) -> ExtractionResult:
    """Extract plain text. One logical page (whole file)."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return ExtractionResult(failure_reason=f"read error: {e}")
    doc = NormalizedDocument(
        full_text=content.strip(),
        pages=[PageBlock(page_index=0, text=content.strip())],
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=1.0,
            page_count=1,
            parser="txt",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)


def extract_md(path: Path, provenance: dict) -> ExtractionResult:
    """Extract Markdown. Preserves structure as-is for downstream parsing."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return ExtractionResult(failure_reason=f"read error: {e}")
    doc = NormalizedDocument(
        full_text=content.strip(),
        pages=[PageBlock(page_index=0, text=content.strip())],
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=1.0,
            page_count=1,
            parser="md",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)
