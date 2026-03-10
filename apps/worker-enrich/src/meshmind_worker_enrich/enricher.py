"""Enrichment: language detection, classification, tags, entities, sensitivity."""

from __future__ import annotations

import logging
from typing import Any

from .models import EnrichmentResult
from .provider import EnrichmentProvider

logger = logging.getLogger(__name__)


def _detect_language(text: str) -> str | None:
    """Deterministic language detection via langdetect."""
    try:
        import langdetect
        return langdetect.detect(text)
    except Exception as e:
        logger.debug("langdetect failed: %s", e)
        return None


def _classify_document_heuristic(text: str, extension: str) -> str:
    """Simple heuristic classification - no LLM."""
    ext_lower = extension.lower()
    if ext_lower in ("pdf", "docx", "doc"):
        return "document"
    if ext_lower in ("xlsx", "xls", "csv"):
        return "spreadsheet"
    if ext_lower in ("jpg", "jpeg", "png", "tiff"):
        return "image"
    return "document"


def enrich_chunk(
    text: str,
    provenance: dict[str, Any],
    provider: EnrichmentProvider | None = None,
) -> EnrichmentResult:
    """
    Enrich a chunk: language (deterministic), optional LLM-based enrichment.
    """
    ext = str(provenance.get("extension", ""))
    lang = _detect_language(text)
    doc_class = _classify_document_heuristic(text, ext)

    result = EnrichmentResult(
        language=lang,
        document_class=doc_class,
        summary=None,
        tags=[],
        entities=[],
        sensitivity_hint=None,
    )

    if provider:
        try:
            extra = provider.enrich(text, provenance)
            if extra:
                result.summary = extra.get("summary")
                result.tags = extra.get("tags") or []
                result.entities = extra.get("entities") or []
                result.sensitivity_hint = extra.get("sensitivity_hint")
        except Exception as e:
            logger.debug("enrichment provider failed: %s", e)

    return result
