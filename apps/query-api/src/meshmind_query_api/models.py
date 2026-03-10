"""Request/response models for query API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --- Search ---

class SearchFilters(BaseModel):
    workspace_ids: list[str] = Field(default_factory=list, description="Scope to workspaces (required)")
    source_ids: list[str] | None = None
    source_types: list[str] | None = None
    date_from: str | None = None
    date_to: str | None = None
    tags: list[str] | None = None
    entities: list[str] | None = None


class SearchResultChunk(BaseModel):
    chunk_id: str
    source_item_id: str
    source_id: str
    workspace_id: str
    text: str
    page_index: int | None = None
    sheet_index: int | None = None
    sheet_name: str | None = None
    score: float
    rank: int
    match_type: str = "hybrid"  # keyword | vector | hybrid
    filename: str | None = None
    open_target: str | None = None


class SearchResult(BaseModel):
    chunks: list[SearchResultChunk]
    facets: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    total: int = 0


# --- Document ---

class DocumentDetail(BaseModel):
    id: str
    source_id: str
    workspace_id: str
    fingerprint: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    chunks: list[dict[str, Any]] = Field(default_factory=list)


# --- Provenance ---

class ProvenanceDetail(BaseModel):
    source_item_id: str
    source_id: str
    workspace_id: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    absolute_path: str | None = None
    filename: str | None = None
    page_index: int | None = None
    sheet_index: int | None = None
    sheet_name: str | None = None
    open_target: str | None = None


# --- Ask ---

class Citation(BaseModel):
    chunk_id: str
    source_item_id: str
    text: str
    page_index: int | None = None
    sheet_index: int | None = None
    sheet_name: str | None = None
    score: float | None = None
    filename: str | None = None
    open_target: str | None = None


class AskRequest(BaseModel):
    question: str
    workspace_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] | None = None
    max_chunks: int = 10


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    source_type: str = "local"  # local | external (future)
    confidence: float | None = None
    coverage: float | None = None
    related_documents: list[str] = Field(default_factory=list)
    grounded: bool = True
