"""MeshMind v2 Query API - search, documents, ask."""

from __future__ import annotations

import logging
import os

import asyncpg
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient

from .config import DATABASE_URL, QDRANT_URL
from .models import AskRequest, AskResponse, SearchResult
from .services.ask_service import ask
from .services.hybrid_search import hybrid_search

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="MeshMind Query API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Lazy connections
_pool = None
_qdrant = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool


def get_qdrant():
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantClient(url=QDRANT_URL)
    return _qdrant


def _parse_workspace_ids(header: str | None) -> list[str]:
    if not header or not header.strip():
        return []
    return [x.strip() for x in header.split(",") if x.strip()]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/search")
async def search_endpoint(
    q: str = Query(..., min_length=1),
    workspace_ids: str | None = Header(None, alias="X-Workspace-Ids"),
    source_ids: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> SearchResult:
    """Hybrid search: keyword (FTS) + vector (Qdrant), RRF merge."""
    wids = _parse_workspace_ids(workspace_ids)
    if not wids:
        raise HTTPException(status_code=403, detail="X-Workspace-Ids header required")
    sids = [x.strip() for x in source_ids.split(",")] if source_ids else None
    pool = await get_pool()
    async with pool.acquire() as conn:
        chunks, facets = await hybrid_search(
            conn, get_qdrant(), q, wids, sids, limit
        )
    return SearchResult(chunks=chunks, facets=facets, total=len(chunks))


@app.post("/ask")
async def ask_endpoint(
    req: AskRequest,
    workspace_ids: str | None = Header(None, alias="X-Workspace-Ids"),
) -> AskResponse:
    """Grounded chat: retrieve chunks, generate answer with citations."""
    wids = req.workspace_ids or _parse_workspace_ids(workspace_ids)
    if not wids:
        raise HTTPException(status_code=403, detail="workspace_ids required")
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await ask(
            conn, get_qdrant(), req.question, wids, req.source_ids, req.max_chunks, req.settings
        )
    return result


def main() -> None:
    import uvicorn
    port = int(os.environ.get("QUERY_API_PORT", "3001"))
    uvicorn.run("meshmind_query_api.main:app", host="0.0.0.0", port=port, reload=True)
