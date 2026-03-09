"""Base worker loop: register -> heartbeat + claim -> process -> complete/fail."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from .client import ClaimedJob, ControlPlaneClient
from .config import WorkerConfig

logger = logging.getLogger(__name__)

ProcessJob = Callable[[ClaimedJob], Awaitable[Any]]
ProcessJobWithClient = Callable[[ControlPlaneClient, ClaimedJob], Awaitable[Any]]


def setup_logging(
    level: str = "INFO",
    format_string: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
) -> None:
    """Configure simple structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=format_string,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


async def run_worker(
    config: WorkerConfig,
    process_job: ProcessJob,
) -> None:
    """Run the worker loop: register, heartbeat in background, claim loop, process jobs.

    - Register with control plane
    - Start heartbeat loop in background (respects heartbeat_interval_secs)
    - Loop: claim job -> process_job(job) -> complete or fail
    - On process_job success: call complete()
    - On process_job exception: call fail() with error message
    """
    async with ControlPlaneClient(
        base_url=config.control_api_url,
        capabilities=config.capabilities,
    ) as client:
        await client.register(config.agent_name, config.capabilities)

        stop = asyncio.Event()
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(client, config.heartbeat_interval_secs, stop)
        )
        try:
            while True:
                job = await client.claim()
                if job is None:
                    await asyncio.sleep(config.claim_interval_secs)
                    continue
                try:
                    await process_job(job)
                    await client.complete(job.job_id, job.job_run_id)
                except Exception as e:
                    logger.exception("job processing failed", extra={"job_id": job.job_id})
                    await client.fail(job.job_id, job.job_run_id, str(e))
        finally:
            stop.set()
            await heartbeat_task


async def _heartbeat_loop(
    client: ControlPlaneClient,
    interval_secs: float,
    stop: asyncio.Event,
) -> None:
    """Send heartbeats at the given interval until stop is set."""
    while not stop.is_set():
        try:
            await client.heartbeat()
            logger.debug("heartbeat sent")
        except Exception:
            logger.exception("heartbeat failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_secs)
        except asyncio.TimeoutError:
            pass


async def run_worker_with_client(
    config: WorkerConfig,
    process_job: ProcessJobWithClient,
) -> None:
    """Like run_worker but passes (client, job) so process_job can call create_source_items, create_job."""
    async with ControlPlaneClient(
        base_url=config.control_api_url,
        agent_id=getattr(config, "agent_id", None),
        capabilities=config.capabilities,
    ) as client:
        if not client.agent_id:
            await client.register(config.agent_name, config.capabilities)
        stop = asyncio.Event()
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(client, config.heartbeat_interval_secs, stop)
        )
        try:
            while True:
                job = await client.claim()
                if job is None:
                    await asyncio.sleep(config.claim_interval_secs)
                    continue
                try:
                    await process_job(client, job)
                    await client.complete(job.job_id, job.job_run_id)
                except Exception as e:
                    logger.exception("job processing failed", extra={"job_id": job.job_id})
                    await client.fail(job.job_id, job.job_run_id, str(e))
        finally:
            stop.set()
            await heartbeat_task
