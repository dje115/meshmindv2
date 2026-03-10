"""Grounded chat/ask service: retrieve chunks, generate answer with citations."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ..config import OLLAMA_URL, MESHMIND_ASK_MODEL
from ..models import AskResponse, Citation
from .hybrid_search import hybrid_search

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You answer questions using only the provided context chunks. 
Cite each claim with [chunk_id] where chunk_id is the identifier before each chunk.
If the context does not contain enough information, say so. Do not invent facts.
Always cite your sources. Format citations as [chunk_id] inline."""

USER_PROMPT_TEMPLATE = """Context chunks:
{chunks}

Question: {question}

Answer (with inline [chunk_id] citations):"""


def _format_chunks_for_prompt(chunks: list[Any]) -> str:
    parts = []
    for c in chunks:
        cid = getattr(c, "chunk_id", c.get("chunk_id", "unknown") if isinstance(c, dict) else "unknown")
        text = getattr(c, "text", c.get("text", "") if isinstance(c, dict) else "")
        parts.append(f"[{cid}]\n{text}")
    return "\n\n---\n\n".join(parts)


def _extract_citations(answer: str, chunks: list[Any]) -> list[Citation]:
    def _get(c, k, default=None):
        return getattr(c, k, c.get(k, default) if isinstance(c, dict) else default)
    by_id = {_get(c, "chunk_id", ""): c for c in chunks}
    cited_ids = set()
    for c in chunks:
        cid = getattr(c, "chunk_id", c.get("chunk_id", ""))
        if cid and f"[{cid}]" in answer:
            cited_ids.add(cid)
    citations = []
    for cid in cited_ids:
        c = by_id.get(cid)
        if not c:
            continue
        citations.append(Citation(
            chunk_id=cid,
            source_item_id=str(_get(c, "source_item_id", "")),
            text=(_get(c, "text", "") or "")[:500],
            page_index=_get(c, "page_index"),
            sheet_index=_get(c, "sheet_index"),
            sheet_name=_get(c, "sheet_name"),
            score=_get(c, "score"),
            filename=_get(c, "filename"),
            open_target=_get(c, "open_target"),
        ))
    return citations


async def ask(
    pool,
    qdrant,
    question: str,
    workspace_ids: list[str],
    source_ids: list[str] | None = None,
    max_chunks: int = 10,
) -> AskResponse:
    if not workspace_ids or not question.strip():
        return AskResponse(
            answer="Please provide a question and ensure you have access to workspaces.",
            grounded=False,
            source_type="local",
        )
    chunks, _ = await hybrid_search(
        pool, qdrant, question, workspace_ids, source_ids, limit=max_chunks
    )
    if not chunks:
        return AskResponse(
            answer="I couldn't find relevant content in your documents. Please try a different question or ensure documents are indexed.",
            citations=[],
            grounded=True,
            source_type="local",
            confidence=0.0,
            coverage=0.0,
        )
    context_str = _format_chunks_for_prompt(chunks)
    user_prompt = USER_PROMPT_TEMPLATE.format(chunks=context_str, question=question.strip())
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL.rstrip('/')}/api/generate",
                json={
                    "model": MESHMIND_ASK_MODEL,
                    "prompt": user_prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                },
            )
            if resp.status_code != 200:
                logger.warning("Ollama error: %s %s", resp.status_code, resp.text[:200])
                return AskResponse(
                    answer="The language model is temporarily unavailable. Please try again later.",
                    citations=[
                        Citation(
                            chunk_id=c.chunk_id,
                            source_item_id=c.source_item_id,
                            text=c.text[:500],
                            page_index=c.page_index,
                            sheet_index=c.sheet_index,
                            sheet_name=c.sheet_name,
                            score=c.score,
                        )
                        for c in chunks[:3]
                    ],
                    grounded=True,
                    source_type="local",
                )
            data = resp.json()
            answer = data.get("response", "").strip()
    except Exception as e:
        logger.exception("Ollama request failed: %s", e)
        return AskResponse(
            answer="The language model is temporarily unavailable. Please ensure Ollama is running.",
            citations=[],
            grounded=False,
            source_type="local",
        )
    citations = _extract_citations(answer, chunks)
    related = list(dict.fromkeys(c.source_item_id for c in chunks))[:5]
    return AskResponse(
        answer=answer,
        citations=citations,
        source_type="local",
        confidence=min(1.0, len(citations) / max(1, len(chunks))) if chunks else 0,
        coverage=len(citations) / max(1, len(chunks)) if chunks else 0,
        related_documents=related,
        grounded=len(citations) > 0,
    )
