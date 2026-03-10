"""Pluggable embedding provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for embedding generation."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier for versioning (e.g. all-MiniLM-L6-v2)."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension."""
        ...

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts. Returns list of vectors."""
        ...
