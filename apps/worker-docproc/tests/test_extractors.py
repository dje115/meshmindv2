"""Fixture-based extraction tests."""

from __future__ import annotations

import pytest
from pathlib import Path

from meshmind_worker_docproc.extractors import EXTRACTORS
from meshmind_worker_docproc.models import ExtractionStatus


PROVENANCE = {
    "source_type": "filesystem",
    "absolute_path": "/tmp/sample.txt",
    "extension": "txt",
}


def test_txt_extraction(fixtures_dir: Path) -> None:
    path = fixtures_dir / "sample.txt"
    result = EXTRACTORS["txt"](path, PROVENANCE)
    assert result.success
    assert result.document is not None
    assert "Sample text file" in result.document.full_text
    assert result.document.extraction_metadata.status == ExtractionStatus.SUCCESS
    assert result.document.extraction_metadata.confidence == 1.0
    assert result.document.provenance == PROVENANCE
    assert len(result.document.pages) == 1
    assert result.document.pages[0].page_index == 0


def test_md_extraction(fixtures_dir: Path) -> None:
    path = fixtures_dir / "sample.md"
    result = EXTRACTORS["md"](path, PROVENANCE)
    assert result.success
    assert "# Sample Markdown" in result.document.full_text
    assert "Section 2" in result.document.full_text


def test_csv_extraction(fixtures_dir: Path) -> None:
    path = fixtures_dir / "sample.csv"
    result = EXTRACTORS["csv"](path, PROVENANCE)
    assert result.success
    assert "alpha" in result.document.full_text
    assert "beta" in result.document.full_text
    assert result.document.pages[0].metadata.get("row_count") == 4


def test_json_extraction(fixtures_dir: Path) -> None:
    path = fixtures_dir / "sample.json"
    result = EXTRACTORS["json"](path, PROVENANCE)
    assert result.success
    assert "Test" in result.document.full_text
    assert "key" in result.document.full_text


def test_doc_returns_result() -> None:
    """DOC uses Tika; returns success when Tika works, structured failure when Tika unavailable."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as f:
        p = Path(f.name)
    try:
        result = EXTRACTORS["doc"](p, PROVENANCE)
        assert result.failure_reason is not None or result.document is not None
        if not result.success:
            assert result.failure_reason is not None
            assert any(
                x in result.failure_reason.lower()
                for x in ("tika", "unreachable", "error", "failed", "timeout")
            )
    finally:
        p.unlink(missing_ok=True)


def test_nonexistent_file_fails() -> None:
    result = EXTRACTORS["txt"](Path("/nonexistent/sample.txt"), PROVENANCE)
    # txt extractor uses read_text which raises OSError - we catch and return failure
    assert not result.success
    assert result.failure_reason is not None
    assert "read error" in result.failure_reason.lower() or "error" in result.failure_reason.lower()


def test_doc_with_existing_file(fixtures_dir: Path) -> None:
    """DOC extractor handles any file via Tika; returns result (success or structured failure)."""
    path = fixtures_dir / "sample.txt"
    result = EXTRACTORS["doc"](path, PROVENANCE)
    assert result.failure_reason is not None or result.document is not None
    if result.success and result.document:
        assert result.document.provenance == PROVENANCE


def test_provenance_preserved(fixtures_dir: Path) -> None:
    prov = {"source_type": "fs", "absolute_path": "/x/y/z", "extension": "txt"}
    result = EXTRACTORS["txt"](fixtures_dir / "sample.txt", prov)
    assert result.success
    assert result.document.provenance == prov


def test_artifacts_schema(fixtures_dir: Path) -> None:
    result = EXTRACTORS["txt"](fixtures_dir / "sample.txt", PROVENANCE)
    arts = result.document.to_artifacts()
    assert "document" in arts
    assert "extraction_metadata" in arts
    assert "downstream_ocr" in arts
    assert "downstream_enrich" in arts
    assert arts["document"]["provenance"] == PROVENANCE
    assert arts["downstream_ocr"] is False
    assert arts["downstream_enrich"] is True
