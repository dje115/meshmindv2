"""Chunking configuration - size, overlap, document-type defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentTypeConfig:
    """Per-document-type chunking parameters."""

    chunk_size: int  # Target chars (approximate tokens ~= chars/4)
    overlap: int
    min_chunk_chars: int = 50
    prefer_sentence_boundaries: bool = True


# Default configs by document type
DEFAULT_PDF = DocumentTypeConfig(chunk_size=600, overlap=100)
DEFAULT_DOCX = DocumentTypeConfig(chunk_size=600, overlap=100)
DEFAULT_SPREADSHEET = DocumentTypeConfig(chunk_size=800, overlap=120)
DEFAULT_IMAGE_OCR = DocumentTypeConfig(chunk_size=500, overlap=80)
DEFAULT_PLAIN = DocumentTypeConfig(chunk_size=600, overlap=100)


@dataclass
class ChunkConfig:
    """Chunking configuration with document-type overrides."""

    defaults: DocumentTypeConfig = field(default_factory=lambda: DEFAULT_PDF)
    by_document_type: dict[str, DocumentTypeConfig] = field(default_factory=lambda: {
        "pdf": DEFAULT_PDF,
        "docx": DEFAULT_DOCX,
        "spreadsheet": DEFAULT_SPREADSHEET,
        "image": DEFAULT_IMAGE_OCR,
        "ocr": DEFAULT_IMAGE_OCR,
        "plain": DEFAULT_PLAIN,
    })

    def for_type(self, doc_type: str) -> DocumentTypeConfig:
        """Get config for document type, fallback to defaults."""
        return self.by_document_type.get(doc_type, self.defaults)
