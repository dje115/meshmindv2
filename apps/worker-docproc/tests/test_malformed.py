"""Malformed file and unsupported type tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from meshmind_worker_docproc.extractors import EXTRACTORS

PROVENANCE = {"extension": "txt"}


def test_malformed_json_returns_failure() -> None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        f.write(b"{ invalid json")
        p = Path(f.name)
    try:
        result = EXTRACTORS["json"](p, PROVENANCE)
        assert not result.success
        assert result.failure_reason is not None
        assert "json" in result.failure_reason.lower() or "parse" in result.failure_reason.lower()
    finally:
        p.unlink()


def test_unsupported_extension_returns_none_extractor() -> None:
    assert EXTRACTORS.get("xyz") is None
    assert EXTRACTORS.get("exe") is None
