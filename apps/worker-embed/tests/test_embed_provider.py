"""Embedding provider tests (mock when sentence-transformers unavailable)."""

from __future__ import annotations


def test_embed_provider_interface() -> None:
    """EmbeddingProvider has required interface."""
    from meshmind_worker_embed.embed_provider import EmbeddingProvider

    class MockProvider(EmbeddingProvider):
        @property
        def model_name(self) -> str:
            return "mock"

        @property
        def dimension(self) -> int:
            return 384

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1] * 384 for _ in texts]

    p = MockProvider()
    assert p.model_name == "mock"
    assert p.dimension == 384
    vecs = p.embed(["hello", "world"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 384
