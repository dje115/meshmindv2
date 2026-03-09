"""Change detection and delete handling tests."""

import tempfile
from pathlib import Path

import pytest

from meshmind_connectors.change_store import ChangeStore
from meshmind_connectors.config import FilesystemConnectorConfig
from meshmind_connectors.scanner import detect_changes, scan_files


def test_change_detection_new_modified_deleted(temp_folder):
    # Store path outside scan folder so state.json is not discovered
    with tempfile.TemporaryDirectory() as tmp:
        store_path = Path(tmp) / "state.json"
        store = ChangeStore(store_path)
        (temp_folder / "a.txt").write_text("v1")
        discovered = scan_files(FilesystemConnectorConfig(path=temp_folder))
        delta = detect_changes(discovered, store)
        assert len(delta.new) == 1
        assert len(delta.modified) == 0
        assert len(delta.deleted_fingerprints) == 0
        # Modify file: fingerprint changes (mtime/size), so we get new + deleted
        (temp_folder / "a.txt").write_text("v2")
        discovered2 = scan_files(FilesystemConnectorConfig(path=temp_folder))
        delta2 = detect_changes(discovered2, store)
        assert len(delta2.new) == 1
        assert len(delta2.deleted_fingerprints) == 1
        # Delete file
        (temp_folder / "a.txt").unlink()
        discovered3 = scan_files(FilesystemConnectorConfig(path=temp_folder))
        delta3 = detect_changes(discovered3, store)
        assert len(delta3.deleted_fingerprints) >= 1


def test_delete_handling_prunes_store(temp_folder):
    with tempfile.TemporaryDirectory() as tmp:
        store_path = Path(tmp) / "state.json"
        store = ChangeStore(store_path)
        (temp_folder / "x.pdf").write_text("a")
        cfg = FilesystemConnectorConfig(path=temp_folder)
        disc = scan_files(cfg)
        detect_changes(disc, store)
        assert len(store.all_fingerprints()) == 1
        (temp_folder / "x.pdf").unlink()
        disc2 = scan_files(cfg)
        delta = detect_changes(disc2, store)
        assert len(delta.deleted_fingerprints) == 1
        assert len(store.all_fingerprints()) == 0
