"""Filesystem connector: watch, discover, fingerprint, submit items, dispatch jobs."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from .change_store import ChangeStore, ScanDelta
from .config import (
    DOCUMENT_EXTENSIONS,
    FilesystemConnectorConfig,
    IMAGE_EXTENSIONS,
)
from .provenance import FilesystemProvenance
from .scanner import detect_changes, scan_files

logger = logging.getLogger(__name__)


def _job_kind_for_extension(ext: str) -> str:
    """Route by file class: document -> docproc, image -> image."""
    ext_lower = ext.lower()
    if ext_lower in IMAGE_EXTENSIONS:
        return "image"
    if ext_lower in DOCUMENT_EXTENSIONS:
        return "docproc"
    return "docproc"


async def run_filesystem_scan(
    config: FilesystemConnectorConfig,
    store: ChangeStore,
    source_id: str,
    agent_id: str,
    agent_identity: str,
    create_items: callable,
    create_job: callable,
    progress: callable | None = None,
) -> dict[str, int]:
    """Run a full scan: discover, detect changes, submit items, dispatch jobs.

    create_items(source_id, items) -> list[dict]  # items: [{fingerprint, provenance}]
    create_job(source_id, source_item_id, job_kind) -> dict
    progress(message, details) optional

    Returns metrics: { discovered, new, modified, deleted, items_created, jobs_dispatched }
    """
    metrics: dict[str, int] = {
        "discovered": 0,
        "new": 0,
        "modified": 0,
        "deleted": 0,
        "items_created": 0,
        "jobs_dispatched": 0,
    }
    discovered = scan_files(config)
    metrics["discovered"] = len(discovered)
    delta = detect_changes(discovered, store)
    metrics["new"] = len(delta.new)
    metrics["modified"] = len(delta.modified)
    metrics["deleted"] = len(delta.deleted_fingerprints)
    to_process: list[tuple[Path, str, dict]] = []
    path_fp_stats: dict[str, tuple[Path, str, dict]] = {}
    for p, fp, s in discovered:
        path_fp_stats[fp] = (p, fp, s)
    for r in delta.new + delta.modified:
        if r.fingerprint in path_fp_stats:
            to_process.append(path_fp_stats[r.fingerprint])
    if progress and to_process:
        await progress(
            f"Processing {len(to_process)} new/modified files",
            {"new": metrics["new"], "modified": metrics["modified"], "deleted": metrics["deleted"]},
        )
    batch: list[dict[str, Any]] = []
    for path, fp, stats in to_process:
        prov = FilesystemProvenance.from_path(
            path=path,
            source_root=config.path,
            fingerprint=fp,
            agent_identity=agent_identity,
            stats=stats,
        )
        batch.append({"fingerprint": fp, "provenance": prov.to_dict()})
        if len(batch) >= config.batch_size:
            created = await create_items(source_id, batch)
            metrics["items_created"] += len(created)
            for item, batch_item in zip(created, batch):
                si_id = item.get("id")
                ext = batch_item.get("provenance", {}).get("extension", "")
                job_kind = _job_kind_for_extension(ext)
                if si_id:
                    await create_job(source_id, si_id, job_kind)
                    metrics["jobs_dispatched"] += 1
            batch = []
            if config.rate_limit_delay_secs > 0:
                await asyncio.sleep(config.rate_limit_delay_secs)
    if batch:
        created = await create_items(source_id, batch)
        metrics["items_created"] += len(created)
        for item, batch_item in zip(created, batch):
            si_id = item.get("id")
            ext = batch_item.get("provenance", {}).get("extension", "")
            job_kind = _job_kind_for_extension(ext)
            if si_id:
                await create_job(source_id, si_id, job_kind)
                metrics["jobs_dispatched"] += 1
    return metrics
