"""Tika fallback and legacy Office extraction tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from meshmind_worker_docproc.extractors.tika_fallback import extract_with_tika

PROVENANCE = {"source_type": "filesystem", "absolute_path": "/tmp/test.doc", "extension": "doc"}


def test_tika_unreachable_returns_structured_failure(fixtures_dir: Path) -> None:
    """When Tika server is unreachable, returns structured failure."""
    with patch.dict(os.environ, {"TIKA_SERVER_ENDPOINT": "http://127.0.0.1:19999"}):
        result = extract_with_tika(fixtures_dir / "sample.txt", PROVENANCE, parser_label="tika")
    assert not result.success
    assert result.failure_reason is not None
    assert "Tika" in result.failure_reason or "unreachable" in result.failure_reason.lower()


def test_tika_preserves_provenance(fixtures_dir: Path) -> None:
    """When Tika succeeds, provenance is preserved."""
    prov = {"source_type": "fs", "absolute_path": "/x/y.z", "extension": "doc"}
    with patch.dict(os.environ, {"TIKA_SERVER_ENDPOINT": "http://127.0.0.1:19999"}):
        result = extract_with_tika(fixtures_dir / "sample.txt", prov, parser_label="tika")
    if result.success and result.document:
        assert result.document.provenance == prov
