"""Provenance metadata model for filesystem-ingested items."""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class FilesystemProvenance:
    """Provenance metadata for a discovered filesystem item.

    Captures enough source metadata for MeshMind to answer:
    - Where did this come from?
    - Which file or system?
    - What original location should be opened or referenced?
    """

    source_type: str = "filesystem"
    source_root: str = ""
    absolute_path: str = ""
    relative_path: str = ""
    filename: str = ""
    extension: str = ""
    file_size_bytes: int = 0
    created_time_iso: str | None = None
    modified_time_iso: str | None = None
    discovery_fingerprint: str = ""
    local_path: str = ""
    hostname: str = ""
    agent_identity: str = ""
    open_target: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-serializable dict for provenance field."""
        return {
            "source_type": self.source_type,
            "source_root": self.source_root,
            "absolute_path": self.absolute_path,
            "relative_path": self.relative_path,
            "filename": self.filename,
            "extension": self.extension,
            "file_size_bytes": self.file_size_bytes,
            "created_time_iso": self.created_time_iso,
            "modified_time_iso": self.modified_time_iso,
            "discovery_fingerprint": self.discovery_fingerprint,
            "local_path": self.local_path,
            "hostname": self.hostname,
            "agent_identity": self.agent_identity,
            "open_target": self.open_target,
        }

    @classmethod
    def from_path(
        cls,
        path: Path,
        source_root: Path,
        fingerprint: str,
        agent_identity: str,
        stats: dict[str, Any] | None = None,
    ) -> FilesystemProvenance:
        """Build provenance from a file path and stats."""
        stats = stats or {}
        abs_path = path.resolve()
        try:
            rel = path.resolve().relative_to(source_root.resolve())
            relative_path = str(rel).replace("\\", "/")
        except ValueError:
            relative_path = str(path).replace("\\", "/")
        # open_target: suitable for provenance display and opening (file:// or path)
        open_target = _path_to_open_target(abs_path)
        return cls(
            source_type="filesystem",
            source_root=str(source_root.resolve()).replace("\\", "/"),
            absolute_path=str(abs_path).replace("\\", "/"),
            relative_path=relative_path,
            filename=path.name,
            extension=path.suffix.lstrip(".").lower() if path.suffix else "",
            file_size_bytes=int(stats.get("st_size", 0)),
            created_time_iso=_timestamp_iso(stats.get("st_ctime")),
            modified_time_iso=_timestamp_iso(stats.get("st_mtime")),
            discovery_fingerprint=fingerprint,
            local_path=str(abs_path).replace("\\", "/"),
            hostname=platform.node() or "",
            agent_identity=agent_identity,
            open_target=open_target,
        )


def _timestamp_iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (OSError, ValueError):
        return None


def _path_to_open_target(path: Path) -> str:
    """Convert path to open_target (file:// URL or UNC path as applicable)."""
    s = str(path.resolve())
    s = s.replace("\\", "/")
    if s.startswith("//"):
        return f"file:{s}"
    if len(s) >= 2 and s[1] == ":":
        return f"file:///{s}"
    return f"file://{s}"
