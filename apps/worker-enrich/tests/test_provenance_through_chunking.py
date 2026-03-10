"""Provenance preservation through chunking."""

from __future__ import annotations

from meshmind_chunking import chunk_document


def test_provenance_through_chunking() -> None:
    """Provenance is retained in chunk metadata."""
    prov = {
        "source_type": "filesystem",
        "absolute_path": "/data/docs/report.pdf",
        "filename": "report.pdf",
        "open_target": "file:///data/docs/report.pdf",
    }
    doc = {
        "full_text": "Report content. " * 50,
        "provenance": prov,
    }
    chunks = chunk_document(doc, "si-abc")
    assert len(chunks) >= 1
    for c in chunks:
        assert c.metadata.provenance == prov
        assert c.metadata.absolute_path == prov["absolute_path"]
        assert c.metadata.open_target == prov["open_target"]
