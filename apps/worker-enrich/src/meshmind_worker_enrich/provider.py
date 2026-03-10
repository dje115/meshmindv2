"""Pluggable enrichment provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EnrichmentProvider(ABC):
    """Abstract interface for LLM-based enrichment (summary, tags, entities)."""

    @abstractmethod
    def enrich(self, text: str, provenance: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """
        Enrich text. Returns dict with optional keys:
        - summary: str
        - tags: list[str]
        - entities: list[dict]
        - sensitivity_hint: str
        Returns None if enrichment unavailable.
        """
        ...
