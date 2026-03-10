"""Hybrid search tests (unit: RRF merge, keyword/vector logic)."""

from __future__ import annotations

import pytest

from meshmind_query_api.services.hybrid_search import _merge_hybrid, _rrf_score
from meshmind_query_api.models import SearchResultChunk


def test_rrf_score() -> None:
    assert _rrf_score([1]) > 0
    assert _rrf_score([1, 1]) > _rrf_score([1])
    assert _rrf_score([1]) > _rrf_score([2])


def test_merge_hybrid_keyword_only() -> None:
    kw = [
        {"chunk_id": "c1", "source_item_id": "s1", "source_id": "src1", "workspace_id": "w1",
         "text": "x", "page_index": None, "sheet_index": None, "sheet_name": None, "score": 0.5, "match_type": "keyword"},
    ]
    vec: list = []
    out = _merge_hybrid(kw, vec, limit=10)
    assert len(out) == 1
    assert out[0].chunk_id == "c1"
    assert out[0].match_type == "keyword"


def test_merge_hybrid_vector_only() -> None:
    kw: list = []
    vec = [
        {"chunk_id": "c2", "source_item_id": "s2", "source_id": "src2", "workspace_id": "w1",
         "text": "y", "page_index": 0, "sheet_index": None, "sheet_name": None, "score": 0.8, "match_type": "vector"},
    ]
    out = _merge_hybrid(kw, vec, limit=10)
    assert len(out) == 1
    assert out[0].chunk_id == "c2"
    assert out[0].match_type == "vector"


def test_merge_hybrid_combines() -> None:
    kw = [
        {"chunk_id": "c1", "source_item_id": "s1", "source_id": "src1", "workspace_id": "w1",
         "text": "a", "page_index": None, "sheet_index": None, "sheet_name": None, "score": 0.3, "match_type": "keyword"},
    ]
    vec = [
        {"chunk_id": "c1", "source_item_id": "s1", "source_id": "src1", "workspace_id": "w1",
         "text": "a", "page_index": None, "sheet_index": None, "sheet_name": None, "score": 0.9, "match_type": "vector"},
    ]
    out = _merge_hybrid(kw, vec, limit=10)
    assert len(out) == 1
    assert out[0].match_type == "hybrid"


def test_merge_hybrid_respects_limit() -> None:
    kw = [
        {"chunk_id": f"c{i}", "source_item_id": "s1", "source_id": "src1", "workspace_id": "w1",
         "text": "x", "page_index": None, "sheet_index": None, "sheet_name": None, "score": 0.1, "match_type": "keyword"}
        for i in range(5)
    ]
    vec: list = []
    out = _merge_hybrid(kw, vec, limit=2)
    assert len(out) == 2
