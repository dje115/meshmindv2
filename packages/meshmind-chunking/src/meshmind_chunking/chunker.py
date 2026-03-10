"""Token-aware chunking with page/sheet reference preservation."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .config import ChunkConfig
from .models import Chunk, ChunkMetadata


def _approx_tokens(text: str) -> int:
    """Approximate token count (chars/4 for typical English)."""
    return max(1, len(text) // 4)


def _split_sentences(text: str) -> list[str]:
    """Simple sentence split on . ! ? followed by space or end."""
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _chunk_text(
    text: str,
    chunk_index_offset: int,
    config: Any,
    base_metadata: ChunkMetadata,
) -> list[Chunk]:
    """Chunk plain text with overlap, prefer sentence boundaries."""
    if not text.strip():
        return []
    chunks: list[Chunk] = []
    size = config.chunk_size
    overlap = config.overlap
    prefer_sentences = config.prefer_sentence_boundaries

    if prefer_sentences:
        sentences = _split_sentences(text)
        current: list[str] = []
        current_len = 0
        chunk_idx = chunk_index_offset
        for sent in sentences:
            sent_len = len(sent) + 1
            if current_len + sent_len > size and current:
                chunk_text = " ".join(current)
                meta = ChunkMetadata(
                    chunk_index=chunk_idx,
                    page_index=base_metadata.page_index,
                    sheet_index=base_metadata.sheet_index,
                    sheet_name=base_metadata.sheet_name,
                    source_type=base_metadata.source_type,
                    provenance=base_metadata.provenance,
                    absolute_path=base_metadata.absolute_path,
                    open_target=base_metadata.open_target,
                    filename=base_metadata.filename,
                    low_confidence=base_metadata.low_confidence,
                    confidence=base_metadata.confidence,
                )
                chunks.append(Chunk(text=chunk_text, metadata=meta))
                # Overlap: keep last sentences that fit in overlap
                overlap_len = 0
                keep: list[str] = []
                for s in reversed(current):
                    if overlap_len + len(s) + 1 <= overlap:
                        keep.insert(0, s)
                        overlap_len += len(s) + 1
                    else:
                        break
                current = keep
                current_len = overlap_len
                chunk_idx += 1
            current.append(sent)
            current_len += sent_len
        if current:
            chunk_text = " ".join(current)
            meta = ChunkMetadata(
                chunk_index=chunk_idx,
                page_index=base_metadata.page_index,
                sheet_index=base_metadata.sheet_index,
                sheet_name=base_metadata.sheet_name,
                source_type=base_metadata.source_type,
                provenance=base_metadata.provenance,
                absolute_path=base_metadata.absolute_path,
                open_target=base_metadata.open_target,
                filename=base_metadata.filename,
                low_confidence=base_metadata.low_confidence,
                confidence=base_metadata.confidence,
            )
            chunks.append(Chunk(text=chunk_text, metadata=meta))
    else:
        # Simple sliding window
        start = 0
        chunk_idx = chunk_index_offset
        while start < len(text):
            end = min(start + size, len(text))
            chunk_text = text[start:end].strip()
            if len(chunk_text) >= config.min_chunk_chars:
                meta = ChunkMetadata(
                    chunk_index=chunk_idx,
                    page_index=base_metadata.page_index,
                    sheet_index=base_metadata.sheet_index,
                    sheet_name=base_metadata.sheet_name,
                    source_type=base_metadata.source_type,
                    provenance=base_metadata.provenance,
                    absolute_path=base_metadata.absolute_path,
                    open_target=base_metadata.open_target,
                    filename=base_metadata.filename,
                    low_confidence=base_metadata.low_confidence,
                    confidence=base_metadata.confidence,
                )
                chunks.append(Chunk(text=chunk_text, metadata=meta))
                chunk_idx += 1
            start = end - overlap if end < len(text) else len(text)
    return chunks


def _build_base_metadata(
    provenance: dict[str, Any],
    page_index: int | None = None,
    sheet_index: int | None = None,
    sheet_name: str | None = None,
    low_confidence: bool = False,
    confidence: float | None = None,
) -> ChunkMetadata:
    return ChunkMetadata(
        chunk_index=0,
        page_index=page_index,
        sheet_index=sheet_index,
        sheet_name=sheet_name,
        source_type=str(provenance.get("source_type", "filesystem")),
        provenance=provenance,
        absolute_path=provenance.get("absolute_path") or provenance.get("local_path"),
        open_target=provenance.get("open_target"),
        filename=provenance.get("filename"),
        low_confidence=low_confidence,
        confidence=confidence,
    )


def _make_chunk_id(source_item_id: str, chunk_index: int, text: str) -> str:
    """Stable chunk ID for deduplication and citation."""
    h = hashlib.sha256(f"{source_item_id}:{chunk_index}:{text}".encode()).hexdigest()
    return f"chunk_{source_item_id[:8]}_{chunk_index}_{h[:12]}"


def chunk_document(
    document: dict[str, Any],
    source_item_id: str,
    doc_type: str = "plain",
    config: ChunkConfig | None = None,
) -> list[Chunk]:
    """
    Chunk a normalized document (from docproc/ocr/image).

    Preserves page_index, sheet_index/sheet_name, provenance.
    """
    config = config or ChunkConfig()
    doc_config = config.for_type(doc_type)
    provenance = document.get("provenance") or {}
    chunks: list[Chunk] = []
    chunk_index_offset = 0

    # Prefer pages if present (PDF, OCR, image)
    pages = document.get("pages") or []
    if pages:
        for i, p in enumerate(pages):
            text = p.get("text") or ""
            if not text.strip():
                continue
            low = p.get("low_confidence", False)
            conf = p.get("confidence")
            base = _build_base_metadata(provenance, page_index=i, low_confidence=low, confidence=conf)
            page_chunks = _chunk_text(text, chunk_index_offset, doc_config, base)
            for c in page_chunks:
                c.metadata.page_index = i
            chunks.extend(page_chunks)
            chunk_index_offset += len(page_chunks)

    # Sheets (spreadsheets)
    sheets = document.get("sheets") or []
    if sheets:
        for i, s in enumerate(sheets):
            text = s.get("text") or ""
            if not text.strip():
                continue
            sheet_name = s.get("sheet_name") or f"Sheet{i + 1}"
            base = _build_base_metadata(
                provenance,
                sheet_index=i,
                sheet_name=sheet_name,
            )
            sheet_chunks = _chunk_text(text, chunk_index_offset, doc_config, base)
            for c in sheet_chunks:
                c.metadata.sheet_index = i
                c.metadata.sheet_name = sheet_name
            chunks.extend(sheet_chunks)
            chunk_index_offset += len(sheet_chunks)

    # Fallback: full_text
    if not chunks:
        full_text = document.get("full_text") or ""
        if full_text.strip():
            base = _build_base_metadata(provenance)
            chunks = _chunk_text(full_text, 0, doc_config, base)

    # Assign chunk_ids
    for c in chunks:
        c.chunk_id = _make_chunk_id(source_item_id, c.metadata.chunk_index, c.text)

    return chunks
