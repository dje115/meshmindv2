"""Job processor: fetch document, chunk, enrich, produce artifacts."""

from __future__ import annotations

import logging
from typing import Any

from meshmind_chunking import ChunkConfig, chunk_document
from meshmind_worker_runtime.client import ClaimedJob, ControlPlaneClient

from .enricher import enrich_chunk
from .provider import EnrichmentProvider

logger = logging.getLogger(__name__)

# Job kinds that produce document artifacts (input for enrich)
INPUT_JOB_KINDS = ["docproc", "ocr", "image"]


def _resolve_doc_type(source_item: dict, document: dict) -> str:
    """Determine document type from source and document."""
    prov = (source_item or {}).get("provenance") or {}
    ext = str(prov.get("extension", "")).lower()
    if ext in ("pdf",):
        # Could be native or OCR - check document
        pages = document.get("document", {}).get("pages") or []
        if pages and any(p.get("low_confidence") for p in pages):
            return "ocr"
        return "pdf"
    if ext in ("docx", "doc"):
        return "docx"
    if ext in ("xlsx", "xls", "csv"):
        return "spreadsheet"
    if ext in ("jpg", "jpeg", "png", "tiff"):
        return "image"
    return "plain"


async def _fetch_input_artifacts(
    client: ControlPlaneClient,
    source_item_id: str,
) -> dict[str, Any] | None:
    """Fetch artifacts from docproc, ocr, or image job."""
    for kind in INPUT_JOB_KINDS:
        try:
            artifacts = await client.get_source_item_artifacts(source_item_id, kind)
            if artifacts:
                return artifacts
        except Exception as e:
            logger.debug("no artifacts for job_kind=%s: %s", kind, e)
    return None


def _chunks_to_artifacts(
    chunks: list,
    source_item_id: str,
    source_id: str,
) -> dict[str, Any]:
    """Convert chunks + enrichment to complete artifacts."""
    chunk_records = []
    for c in chunks:
        rec = {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "chunk_index": c.metadata.chunk_index,
            "page_index": c.metadata.page_index,
            "sheet_index": c.metadata.sheet_index,
            "sheet_name": c.metadata.sheet_name,
            "provenance": c.metadata.provenance,
            "absolute_path": c.metadata.absolute_path,
            "open_target": c.metadata.open_target,
            "filename": c.metadata.filename,
            "low_confidence": c.metadata.low_confidence,
            "confidence": c.metadata.confidence,
        }
        chunk_records.append(rec)
    return {
        "chunks": chunk_records,
        "source_item_id": source_item_id,
        "source_id": source_id,
        "downstream_embed": True,
    }


async def process_enrich_job(
    client: ControlPlaneClient,
    job: ClaimedJob,
    enricher: EnrichmentProvider | None = None,
) -> None:
    """Process enrich job: fetch document, chunk, enrich, complete."""
    source_item = job.source_item
    if not source_item:
        raise ValueError("Enrich job requires source_item")

    source_item_id = str(source_item.get("id", ""))
    if not source_item_id:
        raise ValueError("source_item must have id")

    artifacts = await _fetch_input_artifacts(client, source_item_id)
    if not artifacts:
        raise ValueError("No artifacts found for source_item (tried docproc, ocr, image)")

    doc_obj = artifacts.get("document") or artifacts
    document = doc_obj if isinstance(doc_obj, dict) else {"full_text": str(doc_obj) if doc_obj else ""}
    doc_type = _resolve_doc_type(source_item, artifacts)
    config = ChunkConfig()

    chunks = chunk_document(document, source_item_id, doc_type, config)

    # Optional: enrich each chunk (language detection is per-chunk)
    enriched = []
    for c in chunks:
        er = enrich_chunk(c.text, c.metadata.provenance, enricher)
        enriched.append({
            "chunk": c,
            "enrichment": {
                "language": er.language,
                "document_class": er.document_class,
                "summary": er.summary,
                "tags": er.tags,
                "entities": er.entities,
                "sensitivity_hint": er.sensitivity_hint,
            },
        })

    await client.progress(
        job.job_id,
        job.job_run_id,
        "chunking complete",
        {"chunk_count": len(chunks)},
    )

    output = _chunks_to_artifacts(chunks, source_item_id, job.source_id)
    output["enriched_chunks"] = [
        {
            "chunk_id": e["chunk"].chunk_id,
            "text": e["chunk"].text,
            "metadata": {
                "chunk_index": e["chunk"].metadata.chunk_index,
                "page_index": e["chunk"].metadata.page_index,
                "sheet_index": e["chunk"].metadata.sheet_index,
                "sheet_name": e["chunk"].metadata.sheet_name,
                "provenance": e["chunk"].metadata.provenance,
                "absolute_path": e["chunk"].metadata.absolute_path,
                "open_target": e["chunk"].metadata.open_target,
                "filename": e["chunk"].metadata.filename,
            },
            "enrichment": e["enrichment"],
        }
        for e in enriched
    ]

    await client.complete(job.job_id, job.job_run_id, output)

    # Create embed job for vectorization
    try:
        await client.create_job(job.source_id, source_item_id, "embed")
        logger.info("created downstream embed job", extra={"source_item_id": source_item_id})
    except Exception as e:
        logger.warning("could not create embed job: %s", e)
