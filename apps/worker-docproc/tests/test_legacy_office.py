"""Legacy Office (.doc, .xls) extraction tests.

Optional integration tests using real-world samples. Set MESHTEST_PATH env var
to a folder containing .doc and .xls files (e.g. Tax 16-17.doc, income-tax-report.xls).
If unset, these tests are skipped.
"""

from __future__ import annotations

import os
import pytest
from pathlib import Path

from meshmind_worker_docproc.extractors import EXTRACTORS
from meshmind_worker_docproc.models import ExtractionStatus

PROVENANCE_XLS = {"source_type": "filesystem", "absolute_path": "/tmp/test.xls", "extension": "xls"}
PROVENANCE_DOC = {"source_type": "filesystem", "absolute_path": "/tmp/test.doc", "extension": "doc"}

MESHTEST_PATH = Path(os.environ["MESHTEST_PATH"]) if os.environ.get("MESHTEST_PATH") else None


def test_xls_xlrd_succeeds_on_compatible_file() -> None:
    """xlrd works on standard .xls files (e.g. Tax 16-17.xls)."""
    if not MESHTEST_PATH or not MESHTEST_PATH.exists():
        pytest.skip("MESHTEST_PATH not set or folder not found")
    path = MESHTEST_PATH / "Tax 16-17.xls"
    if not path.exists():
        pytest.skip("Tax 16-17.xls not found")
    result = EXTRACTORS["xls"](path, PROVENANCE_XLS)
    assert result.success
    assert result.document.extraction_metadata.parser == "xlrd"
    assert result.document.provenance == PROVENANCE_XLS
    assert len(result.document.sheets) >= 1


def test_xls_tika_fallback_on_xlrd_failure() -> None:
    """When xlrd fails (e.g. income-tax xls), Tika fallback is attempted."""
    if not MESHTEST_PATH or not MESHTEST_PATH.exists():
        pytest.skip("MESHTEST_PATH not set or folder not found")
    path = MESHTEST_PATH / "income-tax-report-2024-01-09.xls"
    if not path.exists():
        pytest.skip("income-tax-report xls not found")
    result = EXTRACTORS["xls"](path, PROVENANCE_XLS)
    # Either Tika succeeds (parser=tika-xls) or both fail with combined message
    if result.success:
        assert result.document.extraction_metadata.parser in ("xlrd", "tika-xls")
        assert result.document.provenance == PROVENANCE_XLS
    else:
        assert result.failure_reason is not None
        assert "xlrd" in result.failure_reason.lower() or "tika" in result.failure_reason.lower()


def test_doc_tika_integration() -> None:
    """When Tika is available, .doc extraction succeeds."""
    if not MESHTEST_PATH or not MESHTEST_PATH.exists():
        pytest.skip("MESHTEST_PATH not set or folder not found")
    path = MESHTEST_PATH / "Tax 16-17.doc"
    if not path.exists():
        pytest.skip("Tax 16-17.doc not found")
    result = EXTRACTORS["doc"](path, PROVENANCE_DOC)
    if result.success:
        assert result.document.extraction_metadata.parser == "tika-doc"
        assert result.document.provenance == PROVENANCE_DOC
    else:
        assert "Tika" in (result.failure_reason or "") or "unreachable" in (result.failure_reason or "").lower()
