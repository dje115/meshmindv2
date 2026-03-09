"""XLSX and XLS extraction - sheet-aware, tabular content."""

from __future__ import annotations

from pathlib import Path

from ..models import (
    ExtractionMetadata,
    ExtractionStatus,
    NormalizedDocument,
    SheetBlock,
)
from .base import ExtractionResult
from .tika_fallback import extract_with_tika


def _extract_xls_via_tika(
    path: Path, provenance: dict, xlrd_error: str
) -> ExtractionResult:
    """Fallback to Tika when xlrd fails (corrupt, format edge cases)."""
    result = extract_with_tika(path, provenance, parser_label="tika-xls")
    if not result.success and result.failure_reason:
        return ExtractionResult(
            failure_reason=(
                f"xls: xlrd failed ({xlrd_error}); "
                f"Tika fallback also failed: {result.failure_reason}"
            )
        )
    if result.document:
        # Tika returns plain text; model as single sheet for consistency
        doc = result.document
        doc.sheets = [
            SheetBlock(
                sheet_index=0,
                sheet_name="Sheet1",
                text=doc.full_text,
                metadata={"parser": "tika-xls", "xlrd_fallback": True},
            )
        ]
        doc.extraction_metadata.sheet_count = 1
        doc.extraction_metadata.message = (
            "xlrd failed; extracted via Apache Tika fallback. "
            "Sheet structure may be simplified."
        )
    return result


def extract_xlsx(path: Path, provenance: dict) -> ExtractionResult:
    """Extract XLSX: sheet names, tabular content. Formulas become values where read."""
    try:
        import openpyxl

        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    except Exception as e:
        return ExtractionResult(failure_reason=f"xlsx read error: {e}")

    sheets: list[SheetBlock] = []
    all_text_parts: list[str] = []

    for idx, sheet in enumerate(wb.worksheets):
        rows: list[str] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c) if c is not None else "" for c in row]
            line = "\t".join(cells).rstrip("\t")
            if line.strip():
                rows.append(line)
        text = "\n".join(rows)
        name = sheet.title
        sheets.append(SheetBlock(sheet_index=idx, sheet_name=name, text=text))
        all_text_parts.append(f"=== {name} ===\n{text}")

    wb.close()
    full_text = "\n\n".join(all_text_parts)

    doc = NormalizedDocument(
        full_text=full_text,
        sheets=sheets,
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.9,
            sheet_count=len(sheets),
            parser="openpyxl",
            message="Formulas evaluated as values. Complex formatting/macros/embeds not captured.",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)


def extract_xls(path: Path, provenance: dict) -> ExtractionResult:
    """Extract legacy XLS. xlrd first; Apache Tika fallback on failure."""
    try:
        import xlrd

        wb = xlrd.open_workbook(str(path))
    except Exception as e:
        return _extract_xls_via_tika(path, provenance, xlrd_error=str(e))

    sheets: list[SheetBlock] = []
    all_text_parts: list[str] = []

    for idx in range(wb.nsheets):
        sheet = wb.sheet_by_index(idx)
        rows: list[str] = []
        for row_idx in range(sheet.nrows):
            cells = [str(sheet.cell_value(row_idx, c)) for c in range(sheet.ncols)]
            line = "\t".join(cells).rstrip("\t")
            if line.strip():
                rows.append(line)
        text = "\n".join(rows)
        name = sheet.name
        sheets.append(SheetBlock(sheet_index=idx, sheet_name=name, text=text))
        all_text_parts.append(f"=== {name} ===\n{text}")

    full_text = "\n\n".join(all_text_parts)

    doc = NormalizedDocument(
        full_text=full_text,
        sheets=sheets,
        extraction_metadata=ExtractionMetadata(
            status=ExtractionStatus.SUCCESS,
            confidence=0.85,
            sheet_count=len(sheets),
            parser="xlrd",
            message="Legacy XLS. Formulas/macros/embeds not captured. xlrd has known limitations.",
        ),
        provenance=provenance,
    )
    return ExtractionResult(document=doc)
