"""Change detection state store.

Tracks discovered files by fingerprint to detect new, modified, and deleted.
Stored as JSON file for simplicity (stateless worker can persist across runs).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileState:
    """Cached state for a discovered file."""

    fingerprint: str
    path: str
    mtime_ns: int | None = None
    size: int = 0


@dataclass
class ChangeResult:
    """Result of change detection for a single path."""

    path: Path
    fingerprint: str
    status: str  # "new" | "modified" | "unchanged"
    prev_state: FileState | None = None


@dataclass
class ScanDelta:
    """Delta from a scan: new/modified files and deleted fingerprints."""

    new: list[ChangeResult] = field(default_factory=list)
    modified: list[ChangeResult] = field(default_factory=list)
    deleted_fingerprints: list[str] = field(default_factory=list)
    unchanged_count: int = 0


class ChangeStore:
    """File-based change detection state store."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = Path(store_path)
        self._state: dict[str, FileState] = {}
        self._load()

    def _load(self) -> None:
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text(encoding="utf-8"))
                self._state = {
                    fp: FileState(
                        fingerprint=v["fingerprint"],
                        path=v["path"],
                        mtime_ns=v.get("mtime_ns"),
                        size=v.get("size", 0),
                    )
                    for fp, v in data.items()
                }
            except Exception as e:
                logger.warning("change_store load failed, starting fresh: %s", e)
                self._state = {}

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            fp: {
                "fingerprint": s.fingerprint,
                "path": s.path,
                "mtime_ns": s.mtime_ns,
                "size": s.size,
            }
            for fp, s in self._state.items()
        }
        self.store_path.write_text(json.dumps(data, indent=0), encoding="utf-8")

    def get(self, fingerprint: str) -> FileState | None:
        return self._state.get(fingerprint)

    def update(self, fingerprint: str, path: str, mtime_ns: int | None, size: int) -> None:
        self._state[fingerprint] = FileState(
            fingerprint=fingerprint,
            path=path,
            mtime_ns=mtime_ns,
            size=size,
        )
        self._save()

    def remove(self, fingerprint: str) -> None:
        if fingerprint in self._state:
            del self._state[fingerprint]
            self._save()

    def all_fingerprints(self) -> set[str]:
        return set(self._state.keys())

    def prune_deleted(self, current_fingerprints: set[str]) -> list[str]:
        """Remove fingerprints no longer present. Returns list of removed."""
        removed = []
        for fp in list(self._state.keys()):
            if fp not in current_fingerprints:
                self.remove(fp)
                removed.append(fp)
        return removed
