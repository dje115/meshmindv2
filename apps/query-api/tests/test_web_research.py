"""Web research and Ask routing tests."""

from __future__ import annotations

from meshmind_query_api.services.ask_service import (
    _local_strong,
    _question_seems_external,
)


def test_local_strong_empty() -> None:
    assert _local_strong([]) is False


def test_local_strong_weak() -> None:
    chunks = [{"chunk_id": "c1", "score": 0.001}]
    assert _local_strong(chunks) is False


def test_local_strong_strong() -> None:
    chunks = [{"chunk_id": "c1", "score": 0.05}]
    assert _local_strong(chunks) is True


def test_question_seems_external() -> None:
    assert _question_seems_external("What is the current price of Bitcoin?") is True
    assert _question_seems_external("Latest news today") is True
    assert _question_seems_external("What are the key points in my documents?") is False


def test_question_seems_local() -> None:
    assert _question_seems_external("Summarize the main findings") is False
