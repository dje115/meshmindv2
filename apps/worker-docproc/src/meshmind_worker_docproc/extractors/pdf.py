"""PDF extraction with native text vs OCR detection."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    PageBlock,
)
from .base import ExtractionResult

# Threshold: chars per page below this suggests scanned/image PDF
MIN_CHARS_PER_PAGE = 50
# If total extracted text is below this, treat as needs_ocr
MIN_TOTAL_CHARS = 100


def _extract_native(path: Path) -> tuple[list[str], int]:
    """Extract text per page using pypdf. Returns (page_texts, page_count)."""
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    page_texts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        page_texts.append(text)
    return page_texts, page_count


def _is_text_readable(page_texts: list[str], page_count: int) -> bool:
    """Determine if PDF has usable extractable text (vs image-only/scanned)."""
    if page_count == 0:
        return False
    total_chars = sum(len(p) for p in page_texts)
    if total_chars < MIN_TOTAL_CHARS:
        return False
    avg_per_page = total_chars / page_count
    if avg_per_page < MIN_CHARS_PER_PAGE:
        return False
    # Reject if mostly whitespace/non-word
    meaningful = sum(len(re.findall(r"\w+", p)) for p in page_texts)
    if meaningful < 10:
        return False
    return True


def extract_pdf(path: Path, provenance: dict) -> ExtractionResult:
    """Extract PDF. If native text is poor/absent, return needs_ocr for downstream OCR job."""
    try:
        page_texts, page_count = _extract_native(path)
    except Exception as e:
        return ExtractionResult(failure_reason=f"pdf read error: {e}")

    if page_count == 0:
        return ExtractionResult(failure_reason="pdf has no pages")

    if not _is_text_readable(page_texts, page_count):
        doc = NormalizedDocument(
            full_text="",
            pages=[PageBlock(page_index=i, text="", metadata={"needs_ocr": True}) for i in range(page_count)],
            extraction_metadata=ExtractionMetadata(
                status=ExtractionStatus.NEEDS_OCR,
                confidence=0.0,
                page_count=page_count,
                parser="pypdf",
                message="Native text extraction yielded insufficient text; OCR fallback recommended",
            ),
            provenance=provenance,
        )
        return ExtractionResult(document=doc)

    full_text = "\n\n".join(page_texts).strip()
    pages = [PageBlock(page_index=i, text=t) for i, t in enumerate(page_texts)]
    doc = NormalizedDocument(
        full_text=full_text,
        pages=pages,
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.95,
            page_count=page_count,
            parser="pypdf",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)
