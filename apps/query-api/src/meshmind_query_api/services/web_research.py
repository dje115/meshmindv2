"""Web research: search and fetch for external/current factual questions."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from ..config import MESHMIND_WEB_RESEARCH_ENABLED

logger = logging.getLogger(__name__)

# Sync DuckDuckGo search - run in thread to avoid blocking
def _ddg_search_sync(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)
        return []


async def _search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_ddg_search_sync, query, max_results)


def _extract_main_text(html: str, url: str) -> str:
    try:
        import trafilatura

        extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
        if extracted and len(extracted) > 100:
            return extracted[:8000]  # Limit for LLM context
    except Exception as e:
        logger.debug("trafilatura extract failed for %s: %s", url, e)
    # Fallback: strip tags and grab first chunk
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())[:3000]
    return text if text.strip() else ""


@dataclass
class WebCitation:
    title: str
    source: str
    url: str
    snippet: str


async def web_search_and_fetch(
    query: str,
    max_search_results: int = 5,
    max_fetch: int = 3,
    web_research_enabled: bool | None = None,
) -> list[WebCitation]:
    """Search the web and fetch page content. Returns structured citations."""
    enabled = web_research_enabled if web_research_enabled is not None else MESHMIND_WEB_RESEARCH_ENABLED
    if not enabled:
        return []

    results = await _search(query, max_results=max_search_results)
    if not results:
        return []

    citations: list[WebCitation] = []
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for i, r in enumerate(results[:max_fetch]):
            url = r.get("href") or r.get("url") or ""
            if not url or not url.startswith("http"):
                continue
            title = (r.get("title") or r.get("body", "")[:80] or "Untitled").strip()
            snippet = (r.get("body") or r.get("snippet") or "")[:500].strip()
            try:
                parse = urlparse(url)
                source = parse.netloc or url
            except Exception:
                source = url

            # Fetch page for richer content
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = _extract_main_text(resp.text, url)
                    if text and len(text) > len(snippet):
                        snippet = text[:600] + ("…" if len(text) > 600 else "")
            except Exception as e:
                logger.debug("Fetch %s failed: %s", url[:50], e)

            citations.append(WebCitation(
                title=title[:200],
                source=source,
                url=url,
                snippet=snippet or "(No excerpt)",
            ))

    return citations


def is_web_research_available(override: bool | None = None) -> bool:
    """Whether web research is enabled and usable. Use override from request settings if provided."""
    if override is not None:
        return override
    return MESHMIND_WEB_RESEARCH_ENABLED
