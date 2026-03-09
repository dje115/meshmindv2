"""MeshMind v2 Filesystem Connector worker.

Discovers files, fingerprints, captures provenance, and dispatches to docproc/image.
No document extraction, OCR, or LLM enrichment.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from meshmind_worker_runtime import setup_logging
from meshmind_worker_runtime.client import ClaimedJob, ControlPlaneClient
from meshmind_worker_runtime.config import WorkerConfig
from meshmind_worker_runtime.worker import run_worker_with_client

from meshmind_connectors.change_store import ChangeStore
from meshmind_connectors.config import FilesystemConnectorConfig
from meshmind_connectors.filesystem import run_filesystem_scan

logger = logging.getLogger(__name__)


async def process_job(client: ControlPlaneClient, job: ClaimedJob) -> None:
    """Process a claimed filesystem scan job."""
    source_id = job.source_id
    config_dict = job.config or {}
    try:
        fs_config = FilesystemConnectorConfig.from_source_config(config_dict)
    except ValueError as e:
        raise RuntimeError(f"invalid filesystem config: {e}") from e
    store_path = Path(
        os.environ.get("MESHMIND_CHANGE_STORE")
        or f"data/connector-state/{source_id}.json"
    )
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store = ChangeStore(store_path)

    async def create_items(sid: str, items: list) -> list:
        return await client.create_source_items(sid, items)

    async def create_job_fn(sid: str, si_id: str, job_kind: str) -> dict:
        return await client.create_job(sid, si_id, job_kind)

    async def progress_fn(message: str, details: dict) -> None:
        await client.progress(job.job_id, job.job_run_id, message, details)

    agent_id = client.agent_id or ""
    metrics = await run_filesystem_scan(
        config=fs_config,
        store=store,
        source_id=source_id,
        agent_id=agent_id,
        agent_identity=f"filesystem-connector:{agent_id[:8]}",
        create_items=create_items,
        create_job=create_job_fn,
        progress=progress_fn,
    )
    logger.info(
        "scan complete",
        extra={"job_id": job.job_id, "source_id": source_id, "metrics": metrics},
    )


def main() -> None:
    setup_logging()
    config = WorkerConfig.from_env()
    asyncio.run(run_worker_with_client(config, process_job))


if __name__ == "__main__":
    main()
