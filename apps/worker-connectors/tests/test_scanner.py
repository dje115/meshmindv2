"""Filesystem scanner and include/exclude pattern tests."""

from pathlib import Path

import pytest

from meshmind_connectors.config import FilesystemConnectorConfig
from meshmind_connectors.scanner import scan_files


def test_scan_discovers_supported_files(temp_folder):
    (temp_folder / "a.pdf").write_text("x")
    (temp_folder / "b.txt").write_text("y")
    (temp_folder / "c.docx").write_text("z")
    (temp_folder / "skip.xyz").write_text("nope")
    config = FilesystemConnectorConfig(path=temp_folder)
    results = scan_files(config)
    exts = {Path(r[0]).suffix.lower().lstrip(".") for r in results}
    assert "pdf" in exts
    assert "txt" in exts
    assert "docx" in exts
    assert "xyz" not in exts
    assert len(results) == 3


def test_scan_exclude_patterns(temp_folder):
    (temp_folder / "doc.pdf").write_text("x")
    (temp_folder / "node_modules").mkdir()
    (temp_folder / "node_modules" / "pkg.pdf").write_text("y")
    config = FilesystemConnectorConfig(
        path=temp_folder,
        exclude_patterns=["**/node_modules/**"],
    )
    results = scan_files(config)
    paths = [str(r[0]) for r in results]
    assert any("doc.pdf" in p for p in paths)
    assert not any("node_modules" in p for p in paths)


def test_scan_include_patterns(temp_folder):
    (temp_folder / "a.pdf").write_text("x")
    (temp_folder / "b.txt").write_text("y")
    config = FilesystemConnectorConfig(
        path=temp_folder,
        include_patterns=["**/*.pdf"],
    )
    results = scan_files(config)
    assert len(results) == 1
    assert "a.pdf" in str(results[0][0])


def test_scan_max_depth(temp_folder):
    (temp_folder / "a.txt").write_text("x")
    (temp_folder / "sub").mkdir()
    (temp_folder / "sub" / "b.txt").write_text("y")
    (temp_folder / "sub" / "deep").mkdir()
    (temp_folder / "sub" / "deep" / "c.txt").write_text("z")
    config = FilesystemConnectorConfig(path=temp_folder, max_depth=1)
    results = scan_files(config)
    paths = [str(r[0]) for r in results]
    assert any("a.txt" in p for p in paths)
    assert any("b.txt" in p for p in paths)
    assert not any("c.txt" in p for p in paths)


def test_fingerprint_stable(temp_folder):
    (temp_folder / "f.txt").write_text("hello")
    config = FilesystemConnectorConfig(path=temp_folder)
    r1 = scan_files(config)
    r2 = scan_files(config)
    assert len(r1) == 1
    assert r1[0][1] == r2[0][1]


def test_large_folder_batching(temp_folder):
    """Create many files; verify scan respects batch_size concept (scanner returns all, batching is in filesystem.py)."""
    for i in range(15):
        (temp_folder / f"doc{i}.txt").write_text("x")
    config = FilesystemConnectorConfig(path=temp_folder, batch_size=5)
    results = scan_files(config)
    assert len(results) == 15
