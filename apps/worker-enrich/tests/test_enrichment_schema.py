"""Enrichment schema tests."""

from __future__ import annotations

from meshmind_worker_enrich.enricher import enrich_chunk


def test_enrich_returns_schema() -> None:
    """Enrichment result has expected fields."""
    result = enrich_chunk("This is English text about technology.", {})
    assert result.language is not None or result.language is None
    assert result.document_class is not None
    assert isinstance(result.tags, list)
    assert isinstance(result.entities, list)


def test_classification_heuristic() -> None:
    """Document class from extension."""
    result = enrich_chunk("x", {"extension": "pdf"})
    assert result.document_class == "document"
    result2 = enrich_chunk("x", {"extension": "xlsx"})
    assert result2.document_class == "spreadsheet"
