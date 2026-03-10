"""Job processor: fetch chunks, embed, store in Qdrant."""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from meshmind_worker_runtime.client import ClaimedJob, ControlPlaneClient

from .embed_provider import EmbeddingProvider

logger = logging.getLogger(__name__)

COLLECTION_PREFIX = "meshmind"
DEFAULT_QDRANT_URL = "http://localhost:6333"


def _get_provider() -> EmbeddingProvider:
    """Build embedding provider from env."""
    model = os.environ.get("MESHMIND_EMBED_MODEL", "all-MiniLM-L6-v2")
    try:
        from .sentence_provider import SentenceTransformerProvider
        return SentenceTransformerProvider(model_name=model)
    except ImportError:
        raise RuntimeError(
            "Install sentence-transformers: pip install 'meshmind-worker-embed[sentence-transformers]'"
        )


def _collection_name(model_name: str) -> str:
    """Version collection by model."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in model_name)
    return f"{COLLECTION_PREFIX}_{safe}"


def _point_id(source_item_id: str, chunk_index: int, chunk_id: str) -> int:
    """Deterministic stable point ID for Qdrant (u64-safe, no hash())."""
    s = chunk_id if chunk_id else f"{source_item_id}:{chunk_index}"
    h = hashlib.sha256(s.encode()).digest()
    return int.from_bytes(h[:8], "big") % (2**63)


async def process_embed_job(
    client: ControlPlaneClient,
    job: ClaimedJob,
    qdrant_url: str | None = None,
    provider: EmbeddingProvider | None = None,
) -> None:
    """Process embed job: fetch chunks, embed, store in Qdrant."""
    source_item = job.source_item
    if not source_item:
        raise ValueError("Embed job requires source_item")

    source_item_id = str(source_item.get("id", ""))
    if not source_item_id:
        raise ValueError("source_item must have id")

    artifacts = await client.get_source_item_artifacts(source_item_id, "enrich")
    if not artifacts:
        raise ValueError("No enrich artifacts found for source_item")

    raw = artifacts.get("chunks") or artifacts.get("enriched_chunks") or []
    # Normalize to {text, chunk_id, chunk_index, ...}
    chunks = []
    for c in raw:
        if isinstance(c, dict):
            chunks.append(c)
        else:
            chunks.append({"text": str(getattr(c, "text", c)), "chunk_index": len(chunks)})
    if not chunks:
        raise ValueError("No chunks in enrich artifacts")

    provider = provider or _get_provider()
    qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL)

    texts = []
    payloads = []
    for i, c in enumerate(chunks):
        text = c.get("text") or ""
        if not text.strip():
            continue
        texts.append(text)
        payloads.append({
            "chunk_id": c.get("chunk_id", ""),
            "chunk_index": c.get("chunk_index", i),
            "page_index": c.get("page_index"),
            "sheet_index": c.get("sheet_index"),
            "sheet_name": c.get("sheet_name"),
            "source_item_id": source_item_id,
            "source_id": str(job.source_id),
            "metadata": c.get("metadata", c),
        })

    if not texts:
        raise ValueError("No non-empty chunk text to embed")

    await client.progress(
        job.job_id,
        job.job_run_id,
        "embedding",
        {"chunk_count": len(texts)},
    )

    vectors = provider.embed(texts)

    qc = QdrantClient(url=qdrant_url)
    coll_name = _collection_name(provider.model_name)
    try:
        qc.get_collection(coll_name)
    except Exception:
        qc.create_collection(
            coll_name,
            vectors_config=VectorParams(size=provider.dimension, distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=_point_id(source_item_id, p["chunk_index"], p["chunk_id"]),
            vector=v,
            payload={**p, "text": texts[i]},
        )
        for i, (v, p) in enumerate(zip(vectors, payloads))
    ]
    qc.upsert(coll_name, points=points)

    # Index chunks for keyword search (chunk_index)
    index_payload = [
        {
            "chunk_id": p.get("chunk_id", ""),
            "chunk_index": p.get("chunk_index", i),
            "text": texts[i],
            "page_index": p.get("page_index"),
            "sheet_index": p.get("sheet_index"),
            "sheet_name": p.get("sheet_name"),
            "provenance": p.get("metadata", {}).get("provenance", {}),
        }
        for i, p in enumerate(payloads)
    ]
    try:
        await client.index_chunks(source_item_id, index_payload)
    except Exception as e:
        logger.warning("index_chunks failed (non-fatal): %s", e)

    output: dict[str, Any] = {
        "collection": coll_name,
        "model": provider.model_name,
        "points_upserted": len(points),
        "source_item_id": source_item_id,
    }
    await client.complete(job.job_id, job.job_run_id, output)
