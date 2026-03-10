"""Job processor: resolve file, extract metadata, thumbnail, OCR, classify."""

from __future__ import annotations

import logging
from pathlib import Path

import pytesseract
from PIL import Image

from meshmind_worker_runtime.client import ClaimedJob, ControlPlaneClient

from .caption import CaptionProvider
from .classifier import classify_image
from .exif import extract_exif
from .models import ImageCategory, ImageResult
from .thumbnail import generate_thumbnail

logger = logging.getLogger(__name__)

# Confidence threshold for low-confidence OCR
LOW_CONFIDENCE_THRESHOLD = 0.6


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


def _run_ocr(img: Image.Image) -> tuple[str, float]:
    """Run Tesseract OCR on image. Returns (text, mean_confidence)."""
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    text_parts: list[str] = []
    confidences: list[float] = []
    for i in range(len(data["text"])):
        t = (data["text"][i] or "").strip()
        if t:
            text_parts.append(t)
        c = float(data["conf"][i]) if data["conf"][i] != "-1" else 0.0
        if c > 0:
            confidences.append(c / 100.0)
    text = " ".join(text_parts)
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return text, mean_conf


def process_image(
    path: Path,
    provenance: dict,
    caption_provider: CaptionProvider | None = None,
    thumbnail_output_dir: Path | None = None,
) -> ImageResult:
    """Process a single image: EXIF, thumbnail, OCR, classification, optional caption."""
    img = Image.open(path).convert("RGB")
    width, height = img.size

    exif = extract_exif(img)

    thumb_path: Path | None = None
    if thumbnail_output_dir:
        thumb_path = thumbnail_output_dir / f"{path.stem}_thumb.jpg"
    saved_path, thumb_b64 = generate_thumbnail(path, thumb_path)

    ocr_text, ocr_conf = _run_ocr(img)
    ocr_low = ocr_conf < LOW_CONFIDENCE_THRESHOLD

    category = classify_image(width, height, ocr_text, ocr_conf)

    caption: str | None = None
    if caption_provider:
        try:
            caption = caption_provider.caption(path, {"width": width, "height": height})
        except Exception as e:
            logger.debug("caption provider failed: %s", e)

    return ImageResult(
        provenance=provenance,
        exif=exif,
        thumbnail_path=saved_path,
        thumbnail_base64=thumb_b64,
        ocr_text=ocr_text,
        ocr_confidence=ocr_conf,
        ocr_low_confidence=ocr_low,
        category=category,
        caption=caption,
        width=width,
        height=height,
    )


async def process_image_job(
    client: ControlPlaneClient,
    job: ClaimedJob,
    caption_provider: CaptionProvider | None = None,
) -> None:
    """Process an image job."""
    path = _get_file_path(job)
    if not path:
        raise ValueError(
            "No file path in source_item provenance (absolute_path, local_path, or open_target)"
        )

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    provenance = (job.source_item or {}).get("provenance") or {}

    result = process_image(path, provenance, caption_provider=caption_provider)

    await client.progress(
        job.job_id,
        job.job_run_id,
        "image processing complete",
        {"category": result.category.value, "ocr_low_confidence": result.ocr_low_confidence},
    )

    await client.complete(job.job_id, job.job_run_id, result.to_artifacts())

    source_item_id = (job.source_item or {}).get("id")
    if source_item_id:
        try:
            await client.create_job(job.source_id, source_item_id, "enrich")
        except Exception as e:
            logger.warning("could not create enrich job: %s", e)
