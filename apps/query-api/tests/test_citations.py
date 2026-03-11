"""Citation extraction tests."""

from __future__ import annotations

from meshmind_query_api.services.ask_service import _extract_local_citations, _format_chunks_for_prompt


def test_format_chunks() -> None:
    chunks = [
        {"chunk_id": "chunk_abc_0", "text": "Hello world"},
        {"chunk_id": "chunk_def_1", "text": "Goodbye"},
    ]
    s = _format_chunks_for_prompt(chunks)
    assert "[chunk_abc_0]" in s
    assert "Hello world" in s
    assert "[chunk_def_1]" in s
    assert "Goodbye" in s


def test_extract_citations() -> None:
    chunks = [
        {"chunk_id": "c1", "source_item_id": "s1", "text": "A", "page_index": 0},
        {"chunk_id": "c2", "source_item_id": "s2", "text": "B", "page_index": 1},
    ]
    answer = "The answer is based on [c1] and also [c2]."
    citations = _extract_local_citations(answer, chunks)
    assert len(citations) == 2
    ids = {c.chunk_id for c in citations}
    assert ids == {"c1", "c2"}


def test_extract_citations_no_match() -> None:
    chunks = [{"chunk_id": "c1", "source_item_id": "s1", "text": "A"}]
    answer = "No citations here."
    citations = _extract_local_citations(answer, chunks)
    assert len(citations) == 0
