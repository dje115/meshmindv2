"""Regression snapshots for extracted text structure."""

from __future__ import annotations

from pathlib import Path

from meshmind_worker_docproc.extractors import EXTRACTORS

PROVENANCE = {"source_type": "filesystem", "absolute_path": "/fixtures/sample.txt", "extension": "txt"}


def test_txt_snapshot(fixtures_dir: Path) -> None:
    """Regression: TXT extraction produces expected structure."""
    result = EXTRACTORS["txt"](fixtures_dir / "sample.txt", PROVENANCE)
    assert result.success
    doc = result.document
    assert doc.full_text.startswith("Sample text file")
    assert "Line two" in doc.full_text
    assert doc.extraction_metadata.parser == "txt"
    assert doc.extraction_metadata.page_count == 1
    assert len(doc.pages) == 1
    assert doc.pages[0].page_index == 0
    # Snapshot-like: structure must have these keys
    arts = doc.to_artifacts()
    assert "document" in arts
    assert "full_text" in arts["document"]
    assert "pages" in arts["document"]
    assert "provenance" in arts["document"]
    assert "extraction_metadata" in arts
    assert arts["extraction_metadata"]["status"] == "success"
