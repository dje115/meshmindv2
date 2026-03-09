"""Filesystem connector configuration schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Supported file extensions (lowercase)
DOCUMENT_EXTENSIONS = frozenset(
    {
        "pdf",
        "docx",
        "doc",
        "xlsx",
        "xls",
        "txt",
        "md",
        "rtf",
        "html",
        "csv",
        "json",
    }
)

IMAGE_EXTENSIONS = frozenset(
    {
        "jpg",
        "jpeg",
        "png",
        "tiff",
    }
)

SUPPORTED_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS


@dataclass
class FilesystemConnectorConfig:
    """Configuration for a filesystem source.

    Attributes:
        path: Root path to scan (absolute, or resolved).
        include_patterns: Glob patterns for files to include (e.g. ["**/*.pdf"]).
            If empty, all supported extensions under path are included.
        exclude_patterns: Glob patterns to exclude (e.g. ["**/node_modules/**"]).
        max_depth: Maximum recursion depth (0 = path only, -1 = unlimited).
        batch_size: Max items per batch when submitting to control plane.
        rate_limit_delay_secs: Delay between batches (respect control plane limits).
    """

    path: Path
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    max_depth: int = -1
    batch_size: int = 100
    rate_limit_delay_secs: float = 0.1

    @classmethod
    def from_source_config(cls, config: dict[str, Any], path_key: str = "path") -> FilesystemConnectorConfig:
        """Build config from source config JSON (e.g. from control plane)."""
        path_str = config.get(path_key) or config.get("root_path") or ""
        if not path_str:
            raise ValueError("config must include 'path' or 'root_path'")
        path = Path(path_str).resolve()
        return cls(
            path=path,
            include_patterns=config.get("include_patterns") or [],
            exclude_patterns=config.get("exclude_patterns") or ["**/node_modules/**", "**/.git/**"],
            max_depth=int(config.get("max_depth", -1)),
            batch_size=int(config.get("batch_size", 100)),
            rate_limit_delay_secs=float(config.get("rate_limit_delay_secs", 0.1)),
        )
