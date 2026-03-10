"""Job processor: resolve file, run OCR, produce artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

from meshmind_worker_runtime.client import ClaimedJob, ControlPlaneClient

from .ocr_engine import ocr_image, ocr_pdf
from .models import OcrResult

logger = logging.getLogger(__name__)

OCR_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "tif", "bmp", "gif"}


def _get_file_path(job: ClaimedJob) -> Path | None:
    """Resolve file path from source_item provenance."""
    si = job.source_item
    if not si:
        return None
    prov = si.get("provenance") or {}
    path = prov.get("absolute_path") or prov.get("local_path")
    if path:
        return Path(path)
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


def _run_ocr(path: Path, provenance: dict, ext: str) -> OcrResult:
    """Dispatch to PDF or image OCR."""
    if ext == "pdf":
        return ocr_pdf(path, provenance)
    if ext in OCR_IMAGE_EXTENSIONS:
        return ocr_image(path, provenance)
    raise ValueError(f"Unsupported file type for OCR: {ext}")


async def process_ocr_job(client: ControlPlaneClient, job: ClaimedJob) -> None:
    """Process an OCR job: run OCR, complete or fail."""
    path = _get_file_path(job)
    if not path:
        raise ValueError(
            "No file path in source_item provenance (absolute_path, local_path, or open_target)"
        )

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = _get_extension(job)
    provenance = (job.source_item or {}).get("provenance") or {}

    result = _run_ocr(path, provenance, ext)

    await client.progress(
        job.job_id,
        job.job_run_id,
        "OCR complete",
        {
            "page_count": len(result.pages),
            "low_confidence_pages": result.low_confidence_pages,
        },
    )

    artifacts = result.to_artifacts()
    await client.complete(job.job_id, job.job_run_id, artifacts)

    source_item_id = (job.source_item or {}).get("id")
    if source_item_id:
        try:
            await client.create_job(job.source_id, source_item_id, "enrich")
        except Exception as e:
            logger.warning("could not create enrich job: %s", e)
