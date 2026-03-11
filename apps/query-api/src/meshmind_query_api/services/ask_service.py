"""Grounded chat/ask service: retrieve chunks, optional web research, generate answer with citations."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import OLLAMA_URL, MESHMIND_ASK_MODEL
from ..models import AskResponse, AskSettings, Citation, WebCitationModel
from .hybrid_search import hybrid_search
from .web_research import web_search_and_fetch, is_web_research_available

logger = logging.getLogger(__name__)

# Local result strength: RRF score above this = "strong" local
LOCAL_STRONG_SCORE_THRESHOLD = 0.01
LOCAL_MIN_CHUNKS_STRONG = 1

# Heuristic: question seems external/current/general (triggers web when local weak)
EXTERNAL_KEYWORDS = (
    "current", "today", "latest", "now", "recent", "price", "cost", "how much",
    "what is", "who is", "when did", "where is", "definition of", "weather",
)

SYSTEM_PROMPT_LOCAL = """You answer questions using only the provided context chunks.
Cite each claim with [chunk_id] where chunk_id is the identifier before each chunk.
If the context does not contain enough information, say so. Do not invent facts.
Always cite your sources. Format citations as [chunk_id] inline."""

SYSTEM_PROMPT_WEB = """You answer questions using the provided web search results.
Cite each claim with [web_N] where N is the number of the source (1, 2, 3...).
If the context does not contain enough information, say so. Do not invent facts.
Always cite your sources. Format citations as [web_1], [web_2], etc. inline."""

SYSTEM_PROMPT_MIXED = """You answer questions using both local document chunks and web search results.
- For local chunks, cite with [chunk_id].
- For web sources, cite with [web_N] where N is the source number.
If the context does not contain enough information, say so. Do not invent facts.
Always cite your sources."""

USER_PROMPT_LOCAL = """Context chunks:
{chunks}

Question: {question}

Answer (with inline [chunk_id] citations):"""

USER_PROMPT_WEB = """Web search results:
{chunks}

Question: {question}

Answer (with inline [web_N] citations):"""

USER_PROMPT_MIXED = """Local document chunks:
{local_chunks}

Web search results:
{web_chunks}

Question: {question}

Answer (with inline [chunk_id] or [web_N] citations as appropriate):"""


def _format_chunks_for_prompt(chunks: list[Any]) -> str:
    parts = []
    for c in chunks:
        cid = getattr(c, "chunk_id", c.get("chunk_id", "unknown") if isinstance(c, dict) else "unknown")
        text = getattr(c, "text", c.get("text", "") if isinstance(c, dict) else "")
        parts.append(f"[{cid}]\n{text}")
    return "\n\n---\n\n".join(parts)


def _format_web_for_prompt(citations: list[Any]) -> str:
    parts = []
    for i, c in enumerate(citations, 1):
        title = getattr(c, "title", c.get("title", "")) if hasattr(c, "title") else c.get("title", "")
        snippet = getattr(c, "snippet", c.get("snippet", "")) if hasattr(c, "snippet") else c.get("snippet", "")
        url = getattr(c, "url", c.get("url", "")) if hasattr(c, "url") else c.get("url", "")
        parts.append(f"[web_{i}]\n{title}\n{snippet}\nSource: {url}")
    return "\n\n---\n\n".join(parts)


def _extract_local_citations(answer: str, chunks: list[Any]) -> list[Citation]:
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


def _extract_web_citations(answer: str, web: list[Any]) -> list[WebCitationModel]:
    cited = set()
    for i in range(1, len(web) + 1):
        if f"[web_{i}]" in answer:
            cited.add(i)
    out = []
    for i, c in enumerate(web, 1):
        if i not in cited:
            continue
        title = getattr(c, "title", c.get("title", "")) if hasattr(c, "title") else c.get("title", "")
        source = getattr(c, "source", c.get("source", "")) if hasattr(c, "source") else c.get("source", "")
        url = getattr(c, "url", c.get("url", "")) if hasattr(c, "url") else c.get("url", "")
        snippet = getattr(c, "snippet", c.get("snippet", "")) if hasattr(c, "snippet") else c.get("snippet", "")
        out.append(WebCitationModel(title=title, source=source, url=url, snippet=snippet))
    return out


def _local_strong(chunks: list[Any]) -> bool:
    if not chunks:
        return False
    top_score = 0.0
    for c in chunks:
        s = getattr(c, "score", c.get("score", 0)) if hasattr(c, "score") else c.get("score", 0)
        if s is not None:
            top_score = max(top_score, float(s))
    return top_score >= LOCAL_STRONG_SCORE_THRESHOLD and len(chunks) >= LOCAL_MIN_CHUNKS_STRONG


def _question_seems_external(question: str) -> bool:
    q = question.lower().strip()
    return any(kw in q for kw in EXTERNAL_KEYWORDS)


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
            answer_source_type="local",
            source_type="local",
        )

    chunks, _ = await hybrid_search(
        pool, qdrant, question, workspace_ids, source_ids, limit=max_chunks
    )
    local_strong = _local_strong(chunks)
    question_external = _question_seems_external(question)
    web_enabled = settings.web_research_enabled if settings else None
    web_available = is_web_research_available(web_enabled)
    logger.info("Ask: web_research_enabled=%s web_available=%s", web_enabled, web_available)

    # Routing: local | web | mixed
    use_web = web_available and (
        (not local_strong and question_external) or  # Weak local + external question
        (not chunks and question.strip())  # No local at all
    )
    use_local = local_strong or (not use_web and chunks)

    web_citations_raw: list[Any] = []
    if use_web:
        try:
            web_citations_raw = await web_search_and_fetch(
                question, max_search_results=5, max_fetch=3, web_research_enabled=web_enabled
            )
        except Exception as e:
            logger.warning("Web research failed: %s", e)
            web_citations_raw = []
        if not web_citations_raw:
            use_web = False
            logger.warning("Web search returned no results for: %s", question[:50])
            if not chunks:
                return AskResponse(
                    answer="No relevant content found in your documents, and web search returned no results. Try enabling Internet Research in Settings, or ensure DuckDuckGo is accessible.",
                    local_citations=[],
                    web_citations=[],
                    citations=[],
                    grounded=True,
                    answer_source_type="local",
                    source_type="local",
                    confidence=0.0,
                    coverage=0.0,
                )

    # Build context and prompt
    if use_local and use_web:
        source_type = "mixed"
        system = SYSTEM_PROMPT_MIXED
        context = USER_PROMPT_MIXED.format(
            local_chunks=_format_chunks_for_prompt(chunks) if chunks else "(none)",
            web_chunks=_format_web_for_prompt(web_citations_raw) if web_citations_raw else "(none)",
            question=question.strip(),
        )
    elif use_web:
        source_type = "web"
        system = SYSTEM_PROMPT_WEB
        context = USER_PROMPT_WEB.format(
            chunks=_format_web_for_prompt(web_citations_raw),
            question=question.strip(),
        )
    else:
        if not chunks:
            return AskResponse(
                answer="I couldn't find relevant content in your documents. Enable web search in Settings → Internet Research for external questions, or ensure documents are ingested and indexed.",
                local_citations=[],
                web_citations=[],
                citations=[],
                grounded=True,
                answer_source_type="local",
                source_type="local",
                confidence=0.0,
                coverage=0.0,
            )
        source_type = "local"
        system = SYSTEM_PROMPT_LOCAL
        context = USER_PROMPT_LOCAL.format(
            chunks=_format_chunks_for_prompt(chunks),
            question=question.strip(),
        )

    ollama_url = (settings.ollama_url if settings else None) or OLLAMA_URL
    ask_model = (settings.ask_model if settings else None) or MESHMIND_ASK_MODEL
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ollama_url.rstrip('/')}/api/generate",
                json={
                    "model": ask_model,
                    "prompt": context,
                    "system": system,
                    "stream": False,
                },
            )
            if resp.status_code != 200:
                logger.warning("Ollama error: %s %s", resp.status_code, resp.text[:200])
                return AskResponse(
                    answer="The language model is temporarily unavailable. Please try again later.",
                    local_citations=[Citation(
                        chunk_id=c.chunk_id,
                        source_item_id=c.source_item_id,
                        text=c.text[:500],
                        page_index=c.page_index,
                        sheet_index=c.sheet_index,
                        sheet_name=c.sheet_name,
                        score=c.score,
                    ) for c in chunks[:3]] if chunks else [],
                    web_citations=[],
                    citations=[],
                    grounded=True,
                    answer_source_type=source_type,
                    source_type=source_type,
                )
            data = resp.json()
            answer = data.get("response", "").strip()
    except Exception as e:
        logger.exception("Ollama request failed: %s", e)
        return AskResponse(
            answer="The language model is temporarily unavailable. Please ensure Ollama is running.",
            local_citations=[],
            web_citations=[],
            citations=[],
            grounded=False,
            answer_source_type=source_type,
            source_type=source_type,
        )

    local_cits = _extract_local_citations(answer, chunks) if chunks else []
    web_cits = _extract_web_citations(answer, web_citations_raw) if web_citations_raw else []
    citations = local_cits  # Backward compatibility
    related = list(dict.fromkeys(c.source_item_id for c in chunks))[:5] if chunks else []
    confidence = (len(local_cits) + len(web_cits)) / max(1, len(chunks) + len(web_citations_raw))
    coverage = (len(local_cits) + len(web_cits)) / max(1, len(chunks) + len(web_citations_raw))

    return AskResponse(
        answer=answer,
        citations=citations,
        local_citations=local_cits,
        web_citations=[
            WebCitationModel(title=getattr(w, "title", ""), source=getattr(w, "source", ""), url=getattr(w, "url", ""), snippet=getattr(w, "snippet", ""))
            for w in web_citations_raw
        ] if web_citations_raw else [],
        answer_source_type=source_type,
        source_type=source_type,
        confidence=min(1.0, confidence),
        coverage=min(1.0, coverage),
        related_documents=related,
        grounded=len(local_cits) > 0 or len(web_cits) > 0,
    )
