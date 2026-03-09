"""Filesystem scanner: discover, filter, fingerprint, change detection."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from .change_store import ChangeResult, ChangeStore, ScanDelta
from .config import FilesystemConnectorConfig, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


def _normalize_path(p: Path) -> Path:
    """Normalize path for cross-platform consistency."""
    return p.resolve()


def _matches_include(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if path matches any include pattern (relative to root)."""
    if not patterns:
        return True
    import fnmatch

    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = path
    rel_str = str(rel).replace("\\", "/")
    for pat in patterns:
        norm_pat = pat.replace("\\", "/")
        last_part = norm_pat.split("/")[-1]
        if fnmatch.fnmatch(rel_str, norm_pat):
            return True
        if fnmatch.fnmatch(path.name, last_part):
            return True
        # "**/*.pdf" style: match by extension
        if last_part.startswith("*.") and path.suffix.lower() == f".{last_part[2:].lower()}":
            return True
    return False


def _matches_exclude(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if path matches any exclude pattern."""
    if not patterns:
        return False
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = path
    rel_normalized = Path(str(rel).replace("\\", "/"))
    for pat in patterns:
        norm_pat = pat.replace("\\", "/")
        if rel_normalized.match(norm_pat):
            return True
        # Match segment in path (e.g. node_modules in node_modules/pkg.pdf)
        bare = norm_pat.replace("**/", "").replace("/**", "").replace("*", "").strip("/")
        if bare and bare in rel.parts:
            return True
    return False


def _depth_ok(path: Path, root: Path, max_depth: int) -> bool:
    if max_depth < 0:
        return True
    try:
        rel = path.relative_to(root)
        parts = rel.parts
        depth = len(parts) - 1 if parts else 0
        return depth <= max_depth
    except ValueError:
        return True


def _compute_fingerprint(path: Path, stats: dict) -> str:
    """Compute stable fingerprint from path + mtime + size."""
    mtime = stats.get("st_mtime", 0)
    size = stats.get("st_size", 0)
    path_str = str(path.resolve()).replace("\\", "/")
    data = f"{path_str}|{mtime}|{size}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def scan_files(
    config: FilesystemConnectorConfig,
) -> list[tuple[Path, str, dict]]:
    """Discover files under config.path, filtered by include/exclude and extensions.

    Returns list of (path, fingerprint, stats).
    """
    root = _normalize_path(config.path)
    if not root.exists() or not root.is_dir():
        logger.warning("scan root does not exist or is not a directory: %s", root)
        return []
    results: list[tuple[Path, str, dict]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lstrip(".").lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
        if not _depth_ok(path, root, config.max_depth):
            continue
        if config.exclude_patterns and _matches_exclude(path, root, config.exclude_patterns):
            continue
        if config.include_patterns and not _matches_include(path, root, config.include_patterns):
            continue
        try:
            st = path.stat()
            stats = {
                "st_mtime": st.st_mtime,
                "st_size": st.st_size,
                "st_ctime": getattr(st, "st_ctime", st.st_mtime),
            }
        except OSError as e:
            logger.debug("skip (stat failed): %s: %s", path, e)
            continue
        fingerprint = _compute_fingerprint(path, stats)
        results.append((path, fingerprint, stats))
    return results


def detect_changes(
    discovered: list[tuple[Path, str, dict]],
    store: ChangeStore,
) -> ScanDelta:
    """Compare discovered files to store; return new, modified, deleted."""
    delta = ScanDelta()
    current_fps: set[str] = set()
    for path, fp, stats in discovered:
        current_fps.add(fp)
        prev = store.get(fp)
        mtime = stats.get("st_mtime")
        size = stats.get("st_size", 0)
        size = stats.get("st_size", 0)
        mtime_ns: int | None = int(mtime) if mtime is not None else None
        if prev is None:
            delta.new.append(ChangeResult(path=path, fingerprint=fp, status="new"))
            store.update(fp, str(path), mtime_ns, size)
        elif (prev.mtime_ns != mtime_ns) or (prev.size != size):
            delta.modified.append(
                ChangeResult(path=path, fingerprint=fp, status="modified", prev_state=prev)
            )
            store.update(fp, str(path), mtime_ns, size)
        else:
            delta.unchanged_count += 1
    delta.deleted_fingerprints = store.prune_deleted(current_fps)
    return delta
