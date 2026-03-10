"""Embedding provider for query vectorization."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbedProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


def get_provider(model_name: str | None = None) -> EmbedProvider:
    import os
    name = model_name or os.environ.get("MESHMIND_EMBED_MODEL", "all-MiniLM-L6-v2")
    try:
        from sentence_transformers import SentenceTransformer
        class STProvider(EmbedProvider):
            def __init__(self) -> None:
                self._model = SentenceTransformer(name)
                self._dim = self._model.get_sentence_embedding_dimension()
            @property
            def model_name(self) -> str:
                return name
            @property
            def dimension(self) -> int:
                return self._dim
            def embed(self, texts: list[str]) -> list[list[float]]:
                if not texts:
                    return []
                v = self._model.encode(texts, convert_to_numpy=True)
                return [x.tolist() for x in v]
        return STProvider()
    except ImportError:
        raise RuntimeError(
            "sentence-transformers required: pip install sentence-transformers"
        )
