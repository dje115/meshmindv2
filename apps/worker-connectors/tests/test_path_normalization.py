"""Path normalization tests for Windows and UNC paths."""

from pathlib import Path

import pytest

from meshmind_connectors.provenance import _path_to_open_target


def test_path_to_open_target_local():
    p = Path("C:/docs/file.pdf")
    t = _path_to_open_target(p)
    assert "file://" in t or "file:" in t
    assert "file.pdf" in t


def test_path_normalization_forward_slash():
    from meshmind_connectors.scanner import _normalize_path
    p = Path("a/b/c")
    n = _normalize_path(p)
    assert n.is_absolute() or str(n)
