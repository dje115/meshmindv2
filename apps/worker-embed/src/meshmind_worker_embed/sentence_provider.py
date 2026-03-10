"""Sentence-transformers embedding provider (local)."""

from __future__ import annotations

import logging

from .embed_provider import EmbeddingProvider

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class SentenceTransformerProvider(EmbeddingProvider):
    """Local embeddings via sentence-transformers."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._model_name = model_name
        self._model = None
        self._dim: int | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self._dim is None:
            self._ensure_loaded()
            assert self._dim is not None
        return self._dim

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dim = self._model.get_sentence_embedding_dimension()
        except ImportError as e:
            raise RuntimeError(
                "sentence-transformers required. Install: pip install sentence-transformers"
            ) from e

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure_loaded()
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]
