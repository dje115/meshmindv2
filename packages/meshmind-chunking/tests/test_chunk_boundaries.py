"""Chunk boundary and token-aware tests."""

from __future__ import annotations

from meshmind_chunking import ChunkConfig, chunk_document
from meshmind_chunking.config import DocumentTypeConfig


def test_chunk_preserves_page_refs() -> None:
    """Page index is preserved per chunk."""
    doc = {
        "pages": [
            {"page_index": 0, "text": "Page one content. " * 20},
            {"page_index": 1, "text": "Page two content. " * 20},
        ],
        "provenance": {},
    }
    config = ChunkConfig()
    cfg = DocumentTypeConfig(chunk_size=100, overlap=20)
    config.by_document_type["pdf"] = cfg
    chunks = chunk_document(doc, "si-123", "pdf", config)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.metadata.page_index is not None


def test_chunk_preserves_sheet_refs() -> None:
    """Sheet index and name are preserved."""
    doc = {
        "sheets": [
            {"sheet_index": 0, "sheet_name": "Data", "text": "A1 B1 C1. " * 30},
        ],
        "provenance": {},
    }
    chunks = chunk_document(doc, "si-456", "spreadsheet")
    assert len(chunks) >= 1
    for c in chunks:
        assert c.metadata.sheet_index == 0
        assert c.metadata.sheet_name == "Data"


def test_chunk_id_stable() -> None:
    """Chunk IDs are deterministic."""
    doc = {"full_text": "Same text. " * 20, "provenance": {}}
    a = chunk_document(doc, "si-1")
    b = chunk_document(doc, "si-1")
    assert len(a) == len(b)
    for i, (ca, cb) in enumerate(zip(a, b)):
        assert ca.chunk_id == cb.chunk_id


def test_provenance_in_metadata() -> None:
    """Provenance flows to chunk metadata."""
    prov = {"absolute_path": "/data/x.pdf", "filename": "x.pdf", "open_target": "file:///data/x.pdf"}
    doc = {"full_text": "Content here. " * 20, "provenance": prov}
    chunks = chunk_document(doc, "si-1")
    assert len(chunks) >= 1
    assert chunks[0].metadata.absolute_path == "/data/x.pdf"
    assert chunks[0].metadata.filename == "x.pdf"
