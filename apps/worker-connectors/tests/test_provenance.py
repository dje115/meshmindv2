"""Provenance metadata completeness tests."""

from pathlib import Path

import pytest

from meshmind_connectors.provenance import FilesystemProvenance


def test_provenance_completeness(temp_folder):
    f = temp_folder / "sub" / "doc.pdf"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("content")
    source_root = temp_folder
    fingerprint = "abc123"
    agent = "test-agent-1"
    stats = {"st_size": 7, "st_mtime": 1234567890.0, "st_ctime": 1234567880.0}
    prov = FilesystemProvenance.from_path(
        path=f,
        source_root=source_root,
        fingerprint=fingerprint,
        agent_identity=agent,
        stats=stats,
    )
    d = prov.to_dict()
    assert d["source_type"] == "filesystem"
    assert d["source_root"]
    assert "doc.pdf" in d["absolute_path"]
    assert d["filename"] == "doc.pdf"
    assert d["extension"] == "pdf"
    assert d["file_size_bytes"] == 7
    assert d["discovery_fingerprint"] == fingerprint
    assert d["agent_identity"] == agent
    assert d["hostname"]  # platform.node()
    assert "file://" in d["open_target"] or "file:" in d["open_target"]
    assert d["relative_path"]
    assert d["local_path"]
