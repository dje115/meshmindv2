"""Hybrid search: keyword (Postgres FTS) + vector (Qdrant), RRF merge."""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny

from ..config import DATABASE_URL, QDRANT_URL, MESHMIND_EMBED_MODEL
from ..embed_provider import get_provider
from ..models import SearchResultChunk

logger = logging.getLogger(__name__)

COLLECTION_PREFIX = "meshmind"
K = 60  # RRF constant


def _collection_name(model_name: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in model_name)
    return f"{COLLECTION_PREFIX}_{safe}"


def _rrf_score(ranks: list[int]) -> float:
    return sum(1.0 / (K + r) for r in ranks)


async def _keyword_search(
    pool,
    q: str,
    workspace_ids: list[str],
    source_ids: list[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    if not workspace_ids or not q.strip():
        return []
    if source_ids:
        sql = """
            SELECT ci.chunk_id, ci.source_item_id::text, ci.source_id::text, ci.workspace_id::text,
                   ci.text, ci.page_index, ci.sheet_index, ci.sheet_name,
                   ci.provenance,
                   ts_rank(ci.search_vector, plainto_tsquery('english', $1)) AS score
            FROM chunk_index ci
            WHERE ci.workspace_id::text = ANY($2::text[])
              AND ci.source_id::text = ANY($4::text[])
              AND ci.search_vector @@ plainto_tsquery('english', $1)
            ORDER BY score DESC
            LIMIT $3
        """
        rows = await pool.fetch(sql, q.strip(), workspace_ids, limit, source_ids)
    else:
        sql = """
            SELECT ci.chunk_id, ci.source_item_id::text, ci.source_id::text, ci.workspace_id::text,
                   ci.text, ci.page_index, ci.sheet_index, ci.sheet_name,
                   ci.provenance,
                   ts_rank(ci.search_vector, plainto_tsquery('english', $1)) AS score
            FROM chunk_index ci
            WHERE ci.workspace_id::text = ANY($2::text[])
              AND ci.search_vector @@ plainto_tsquery('english', $1)
            ORDER BY score DESC
            LIMIT $3
        """
        rows = await pool.fetch(sql, q.strip(), workspace_ids, limit)
    result = []
    for r in rows:
        prov = r.get("provenance") or {}
        if isinstance(prov, dict):
            fn = prov.get("filename") or (str(prov.get("absolute_path", "")).split("/")[-1] or None)
            ot = prov.get("open_target") if isinstance(prov.get("open_target"), str) else None
        else:
            fn, ot = None, None
        result.append({
            "chunk_id": r["chunk_id"],
            "source_item_id": str(r["source_item_id"]),
            "source_id": str(r["source_id"]),
            "workspace_id": r["workspace_id"],
            "text": r["text"],
            "page_index": r["page_index"],
            "sheet_index": r["sheet_index"],
            "sheet_name": r["sheet_name"],
            "score": float(r["score"] or 0),
            "match_type": "keyword",
            "filename": fn,
            "open_target": ot,
        })
    return result


async def _source_id_to_workspace(pool, source_ids: list[str]) -> dict[str, str]:
    if not source_ids:
        return {}
    rows = await pool.fetch(
        "SELECT id::text, workspace_id::text FROM sources WHERE id::text = ANY($1::text[])",
        source_ids,
    )
    return {r["id"]: r["workspace_id"] for r in rows}


async def _vector_search(
    pool,
    qdrant: QdrantClient,
    embed_provider,
    q: str,
    allowed_source_ids: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    if not allowed_source_ids:
        return []
    coll = _collection_name(embed_provider.model_name)
    try:
        qdrant.get_collection(coll)
    except Exception:
        logger.warning("Collection %s not found, vector search returns empty", coll)
        return []
    query_vec = embed_provider.embed([q])[0]
    must = [FieldCondition(key="source_id", match=MatchAny(any=allowed_source_ids))]
    results = qdrant.search(
        collection_name=coll,
        query_vector=query_vec,
        query_filter=Filter(must=must),
        limit=limit,
        with_payload=True,
    )
    sid_to_ws = await _source_id_to_workspace(pool, allowed_source_ids)
    out = []
    for p in results:
        pl = p.payload or {}
        meta = pl.get("metadata") or {}
        prov = meta.get("provenance") or {}
        if isinstance(prov, dict):
            fn = prov.get("filename") or (str(prov.get("absolute_path", "")).split("/")[-1] or None)
            ot = prov.get("open_target") if isinstance(prov.get("open_target"), str) else None
        else:
            fn, ot = None, None
        out.append({
            "chunk_id": pl.get("chunk_id", ""),
            "source_item_id": str(pl.get("source_item_id", "")),
            "source_id": str(pl.get("source_id", "")),
            "workspace_id": sid_to_ws.get(str(pl.get("source_id", "")), ""),
            "text": pl.get("text", ""),
            "page_index": pl.get("page_index"),
            "sheet_index": pl.get("sheet_index"),
            "sheet_name": pl.get("sheet_name"),
            "score": p.score or 0,
            "match_type": "vector",
            "filename": fn,
            "open_target": ot,
        })
    return out


def _merge_hybrid(
    keyword_hits: list[dict],
    vector_hits: list[dict],
    limit: int,
) -> list[SearchResultChunk]:
    by_key = {}
    for r, src in [(keyword_hits, "keyword"), (vector_hits, "vector")]:
        for rank, row in enumerate(r, 1):
            key = (row["chunk_id"], row["source_item_id"])
            if key not in by_key:
                by_key[key] = {**row, "ranks": [], "sources": []}
            by_key[key]["ranks"].append(rank)
            if src not in by_key[key]["sources"]:
                by_key[key]["sources"].append(src)
    scored = []
    for row in by_key.values():
        ranks = row["ranks"]
        rrf = _rrf_score(ranks)
        match_type = "hybrid" if len(row["sources"]) > 1 else row["sources"][0]
        scored.append((rrf, {
            **row,
            "rrf_score": rrf,
            "match_type": match_type,
        }))
    scored.sort(key=lambda x: -x[0])
    return [
        SearchResultChunk(
            chunk_id=r["chunk_id"],
            source_item_id=r["source_item_id"],
            source_id=r["source_id"],
            workspace_id=r["workspace_id"],
            text=r["text"],
            page_index=r.get("page_index"),
            sheet_index=r.get("sheet_index"),
            sheet_name=r.get("sheet_name"),
            score=round(r["rrf_score"], 6),
            rank=i + 1,
            match_type=r["match_type"],
            filename=r.get("filename"),
            open_target=r.get("open_target"),
        )
        for i, (_, r) in enumerate(scored[:limit])
    ]


async def _source_ids_for_workspaces(pool, workspace_ids: list[str]) -> list[str]:
    if not workspace_ids:
        return []
    rows = await pool.fetch(
        "SELECT id::text FROM sources WHERE workspace_id::text = ANY($1::text[])",
        workspace_ids,
    )
    return [r["id"] for r in rows]


async def hybrid_search(
    pool,
    qdrant: QdrantClient,
    q: str,
    workspace_ids: list[str],
    source_ids: list[str] | None = None,
    limit: int = 20,
) -> tuple[list[SearchResultChunk], dict]:
    if not workspace_ids:
        return [], {}
    allowed_source_ids = source_ids or await _source_ids_for_workspaces(pool, workspace_ids)
    provider = get_provider()
    keyword_hits = await _keyword_search(pool, q, workspace_ids, source_ids, limit * 2)
    vector_hits = await _vector_search(pool, qdrant, provider, q, allowed_source_ids, limit * 2)
    merged = _merge_hybrid(keyword_hits, vector_hits, limit)
    facets: dict[str, list] = {}
    if merged:
        source_counts: dict[str, int] = {}
        for c in merged:
            source_counts[c.source_id] = source_counts.get(c.source_id, 0) + 1
        facets["source_id"] = [{"value": k, "count": v} for k, v in source_counts.items()]
    return merged, facets
