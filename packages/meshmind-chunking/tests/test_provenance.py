"""Provenance and source location tests."""

from __future__ import annotations

from meshmind_chunking import chunk_document


def test_open_target_preserved() -> None:
    """open_target enables 'open original file' flow."""
    doc = {
        "pages": [{"page_index": 0, "text": "Page 1. " * 30}],
        "provenance": {
            "open_target": "file:///C:/docs/file.pdf",
            "absolute_path": "C:/docs/file.pdf",
        },
    }
    chunks = chunk_document(doc, "si-1")
    assert all(c.metadata.open_target == "file:///C:/docs/file.pdf" for c in chunks)
