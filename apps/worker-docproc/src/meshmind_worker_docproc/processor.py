"""Job processor: resolve file, extract, produce artifacts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from meshmind_worker_runtime.client import ClaimedJob, ControlPlaneClient

from .extractors import EXTRACTORS
from .models import ExtractionStatus, NormalizedDocument

logger = logging.getLogger(__name__)


def _get_file_path(job: ClaimedJob) -> Path | None:
    """Resolve file path from source_item provenance."""
    si = job.source_item
    if not si:
        return None
    prov = si.get("provenance") or {}
    path = prov.get("absolute_path") or prov.get("local_path")
    if path:
        return Path(path)
    # Fallback: open_target may be file:///path
    target = prov.get("open_target", "")
    if target.startswith("file:///"):
        return Path(target[8:].lstrip("/"))
    if target.startswith("file://"):
        return Path(target[7:])
    if target and not target.startswith("http"):
        return Path(target)
    return None


def _get_extension(job: ClaimedJob) -> str:
    """Get file extension from provenance, lowercased."""
    si = job.source_item or {}
    prov = si.get("provenance") or {}
    ext = (prov.get("extension") or "").strip().lower()
    if ext:
        return ext
    path = _get_file_path(job)
    if path and path.suffix:
        return path.suffix.lstrip(".").lower()
    return ""


async def process_docproc_job(client: ControlPlaneClient, job: ClaimedJob) -> None:
    """Process a docproc job: extract document, complete or fail, optionally create downstream jobs."""
    path = _get_file_path(job)
    if not path:
        raise ValueError("No file path in source_item provenance (absolute_path, local_path, or open_target)")

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = _get_extension(job)
    extractor = EXTRACTORS.get(ext)
    if not extractor:
        raise ValueError(f"Unsupported file type: {ext}")

    provenance = (job.source_item or {}).get("provenance") or {}

    result = extractor(path, provenance)

    if result.failure_reason and not result.document:
        raise RuntimeError(result.failure_reason)

    assert result.document is not None
    doc = result.document

    artifacts = doc.to_artifacts()

    await client.progress(
        job.job_id,
        job.job_run_id,
        "extraction complete",
        {"status": doc.extraction_metadata.status.value},
    )

    await client.complete(job.job_id, job.job_run_id, artifacts)

    source_item_id = (job.source_item or {}).get("id")
    if source_item_id and doc.extraction_metadata.status == ExtractionStatus.NEEDS_OCR:
        try:
            await client.create_job(job.source_id, source_item_id, "ocr")
            logger.info("created downstream OCR job", extra={"source_item_id": source_item_id})
        except Exception as e:
            logger.warning("could not create OCR job: %s", e)

    # When extraction succeeds, downstream enrichment/chunking would be a separate job kind.
    # Currently only docproc/image/ocr exist; no "enrich" job. Artifacts include
    # downstream_enrich: true for consumers to trigger chunking.
