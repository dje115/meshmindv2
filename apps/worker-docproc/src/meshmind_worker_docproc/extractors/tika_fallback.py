"""Apache Tika fallback extraction via direct HTTP to Tika server."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import httpx

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    PageBlock,
    SheetBlock,
)
from .base import ExtractionResult

logger = logging.getLogger(__name__)

DEFAULT_TIKA_ENDPOINT = "http://localhost:9998"
DEFAULT_TIMEOUT = 60.0


def _get_tika_endpoint() -> str:
    return os.environ.get("TIKA_SERVER_ENDPOINT", DEFAULT_TIKA_ENDPOINT).rstrip("/")


def _get_tika_timeout() -> float:
    try:
        return float(os.environ.get("TIKA_TIMEOUT_SECS", DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def extract_with_tika(path: Path, provenance: dict, parser_label: str = "tika") -> ExtractionResult:
    """Extract text from a file using Apache Tika server.

    Uses PUT /tika with Accept: text/plain. Requires a running Tika server
    (TIKA_SERVER_ENDPOINT, default http://localhost:9998).

    Returns structured failure when:
    - Tika server is unreachable
    - Parsing fails (corrupt, encrypted, unsupported)
    """
    endpoint = _get_tika_endpoint()
    url = f"{endpoint}/tika"
    timeout = _get_tika_timeout()

    try:
        content = path.read_bytes()
    except OSError as e:
        return ExtractionResult(failure_reason=f"read error: {e}")

    try:
        resp = httpx.put(
            url,
            content=content,
            headers={"Accept": "text/plain"},
            timeout=timeout,
        )
    except httpx.ConnectError as e:
        return ExtractionResult(
            failure_reason=(
                f"Tika server unreachable at {endpoint}: {e}. "
                "Ensure Apache Tika server is running and TIKA_SERVER_ENDPOINT is set correctly."
            )
        )
    except httpx.TimeoutException as e:
        return ExtractionResult(
            failure_reason=f"Tika request timed out ({timeout}s): {e}"
        )
    except Exception as e:
        return ExtractionResult(failure_reason=f"Tika request failed: {e}")

    if resp.status_code == 200:
        text = (resp.text or "").strip()
        doc = NormalizedDocument(
            full_text=text,
            pages=[PageBlock(page_index=0, text=text, metadata={"parser": parser_label})],
            extraction_metadata=ExtractionMetadata(
                status=ExtractionStatus.SUCCESS,
                confidence=0.85,
                page_count=1,
                parser=parser_label,
                message="Extracted via Apache Tika server",
            ),
            provenance=provenance,
        )
        return ExtractionResult(document=doc)

    # Tika returns 415 for unsupported format, 500 for parse errors, etc.
    body_preview = (resp.text or "")[:200].replace("\n", " ")
    if resp.status_code == 415:
        return ExtractionResult(
            failure_reason=f"Tika: unsupported format or content type (415): {body_preview}"
        )
    if resp.status_code == 500:
        return ExtractionResult(
            failure_reason=f"Tika: parsing failed (corrupt, encrypted, or unsupported): {body_preview}"
        )
    return ExtractionResult(
        failure_reason=f"Tika: HTTP {resp.status_code}: {body_preview}"
    )
