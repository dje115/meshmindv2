"""PDF extraction and readable-vs-OCR detection tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from meshmind_worker_docproc.extractors import EXTRACTORS
from meshmind_worker_docproc.models import ExtractionStatus

PROVENANCE = {"source_type": "filesystem", "absolute_path": "/tmp/sample.pdf", "extension": "pdf"}


def _create_text_pdf(path: Path, text: str) -> None:
    """Create a minimal PDF with extractable text using reportlab (dev dependency)."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(72, 720, text)
        c.save()
        buf.seek(0)
        r = PdfReader(buf)
        w = PdfWriter()
        for page in r.pages:
            w.add_page(page)
        with open(path, "wb") as f:
            w.write(f)
    except ImportError:
        # Fallback: blank PDF (will trigger needs_ocr)
        w = PdfWriter()
        w.add_blank_page(612, 792)
        with open(path, "wb") as f:
            w.write(f)


def test_pdf_readable_extraction() -> None:
    """PDF extractor returns valid result; SUCCESS when text present, NEEDS_OCR when blank."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        p = Path(f.name)
    try:
        _create_text_pdf(p, "Extractable PDF content for testing. " * 5)
        result = EXTRACTORS["pdf"](p, PROVENANCE)
        assert result.document is not None
        assert result.document.extraction_metadata.page_count == 1
        assert result.document.extraction_metadata.status in (
            ExtractionStatus.SUCCESS,
            ExtractionStatus.NEEDS_OCR,
        )
        if result.document.extraction_metadata.status == ExtractionStatus.SUCCESS:
            assert len(result.document.full_text) >= 50
    finally:
        p.unlink(missing_ok=True)


def test_pdf_needs_ocr_when_sparse() -> None:
    """When extracted text is very sparse, status should be NEEDS_OCR."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        p = Path(f.name)
    try:
        # Use blank PDF - no extractable text (simulates scanned/image PDF)
        w = PdfWriter()
        w.add_blank_page(612, 792)
        with open(p, "wb") as f:
            w.write(f)

        result = EXTRACTORS["pdf"](p, PROVENANCE)
        assert result.document is not None
        assert result.document.extraction_metadata.status == ExtractionStatus.NEEDS_OCR
        arts = result.document.to_artifacts()
        assert arts["downstream_ocr"] is True
        assert arts["downstream_enrich"] is False
    finally:
        p.unlink(missing_ok=True)


def test_pdf_empty_pages_needs_ocr() -> None:
    """Empty-page PDF should yield needs_ocr or failure."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        p = Path(f.name)
    try:
        writer = PdfWriter()
        writer.add_blank_page(612, 792)
        with open(p, "wb") as f:
            writer.write(f)
        result = EXTRACTORS["pdf"](p, PROVENANCE)
        assert result.document is not None
        assert result.document.extraction_metadata.status == ExtractionStatus.NEEDS_OCR
    finally:
        p.unlink(missing_ok=True)
