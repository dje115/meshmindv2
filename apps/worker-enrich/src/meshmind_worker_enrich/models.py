"""Enrichment output schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnrichmentResult:
    """Structured enrichment for a chunk or document."""

    language: str | None = None
    document_class: str | None = None
    summary: str | None = None
    tags: list[str] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    sensitivity_hint: str | None = None  # e.g. "public", "internal", "confidential"
