"""Chunk and metadata models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChunkMetadata:
    """Stable metadata for citation and provenance."""

    chunk_index: int
    page_index: int | None = None
    sheet_index: int | None = None
    sheet_name: str | None = None
    source_type: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    # For open-original linkage
    absolute_path: str | None = None
    open_target: str | None = None
    filename: str | None = None
    # OCR/image specific
    low_confidence: bool = False
    confidence: float | None = None


@dataclass
class Chunk:
    """A single text chunk with stable metadata."""

    text: str
    metadata: ChunkMetadata
    chunk_id: str = ""  # Stable hash: source_item_id + chunk_index + content_hash
