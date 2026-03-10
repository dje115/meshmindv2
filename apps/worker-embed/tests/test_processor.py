"""Processor tests: point ID determinism."""

from __future__ import annotations

from meshmind_worker_embed.processor import _point_id


def test_point_id_deterministic() -> None:
    """Point IDs are stable across calls (no Python hash())."""
    a = _point_id("item-1", 0, "chunk_item1_0_abc123")
    b = _point_id("item-1", 0, "chunk_item1_0_abc123")
    assert a == b


def test_point_id_differs_by_chunk() -> None:
    """Different chunks produce different point IDs."""
    id1 = _point_id("item-1", 0, "chunk_item1_0_abc")
    id2 = _point_id("item-1", 1, "chunk_item1_1_def")
    assert id1 != id2


def test_point_id_fallback_without_chunk_id() -> None:
    """Uses source_item_id:chunk_index when chunk_id is empty."""
    a = _point_id("item-1", 0, "")
    b = _point_id("item-1", 0, "")
    assert a == b


def test_point_id_u64_safe() -> None:
    """IDs fit in u64 (positive int)."""
    pid = _point_id("item", 999, "chunk_x")
    assert isinstance(pid, int)
    assert 0 <= pid < 2**63
