"""Legacy DOC extraction via Apache Tika."""

from __future__ import annotations

from pathlib import Path

from .base import ExtractionResult
from .tika_fallback import extract_with_tika


def extract_doc(path: Path, provenance: dict) -> ExtractionResult:
    """Extract legacy .doc (Word 97-2003) via Apache Tika server.

    Requires TIKA_SERVER_ENDPOINT (default http://localhost:9998).
    Returns structured failure when Tika is unavailable or parsing fails
    (corrupt, encrypted, unsupported).
    """
    return extract_with_tika(path, provenance, parser_label="tika-doc")
