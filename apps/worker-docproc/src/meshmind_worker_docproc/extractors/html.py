"""HTML extraction using BeautifulSoup."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    PageBlock,
)
from .base import ExtractionResult


def extract_html(path: Path, provenance: dict) -> ExtractionResult:
    """Extract HTML to readable text. Structure simplified for retrieval."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return ExtractionResult(failure_reason=f"read error: {e}")

    soup = BeautifulSoup(content, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Normalize whitespace
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    full_text = "\n".join(lines)

    doc = NormalizedDocument(
        full_text=full_text,
        pages=[PageBlock(page_index=0, text=full_text)],
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.9,
            page_count=1,
            parser="beautifulsoup4",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)
