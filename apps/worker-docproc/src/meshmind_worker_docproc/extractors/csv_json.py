"""CSV and JSON extraction - structured text summaries for retrieval."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    PageBlock,
)
from .base import ExtractionResult


def extract_csv(path: Path, provenance: dict) -> ExtractionResult:
    """Extract CSV as tabular text summary (header + rows)."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return ExtractionResult(failure_reason=f"read error: {e}")

    reader = csv.reader(content.splitlines())
    rows = list(reader)
    if not rows:
        text = ""
    else:
        lines = ["\t".join(cell for cell in row) for row in rows]
        text = "\n".join(lines)

    doc = NormalizedDocument(
        full_text=text,
        pages=[PageBlock(page_index=0, text=text, metadata={"row_count": len(rows)})],
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.95,
            page_count=1,
            parser="csv",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)


def extract_json(path: Path, provenance: dict) -> ExtractionResult:
    """Extract JSON as structured text (keys + stringifiable values for retrieval)."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return ExtractionResult(failure_reason=f"read error: {e}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return ExtractionResult(failure_reason=f"json parse error: {e}")

    def _to_summary(obj: object, depth: int = 0) -> str:
        indent = "  " * depth
        if obj is None:
            return "null"
        if isinstance(obj, bool):
            return str(obj).lower()
        if isinstance(obj, (int, float)):
            return str(obj)
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            parts = [f"{indent}{k}: {_to_summary(v, depth + 1)}" for k, v in obj.items()]
            return "\n".join(parts)
        if isinstance(obj, list):
            parts = [f"{indent}- {_to_summary(v, depth + 1)}" for v in obj[:100]]
            if len(obj) > 100:
                parts.append(f"{indent}... ({len(obj)} items)")
            return "\n".join(parts)
        return str(obj)

    text = _to_summary(data)

    doc = NormalizedDocument(
        full_text=text,
        pages=[PageBlock(page_index=0, text=text)],
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.9,
            page_count=1,
            parser="json",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)
