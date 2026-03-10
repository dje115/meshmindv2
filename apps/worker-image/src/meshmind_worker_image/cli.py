"""CLI entry point for image worker."""

from __future__ import annotations

import asyncio
import logging
import os

from meshmind_worker_runtime.config import WorkerConfig
from meshmind_worker_runtime.worker import run_worker_with_client, setup_logging

from .processor import process_image_job

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def main() -> None:
    config = WorkerConfig.from_env()
    config.capabilities = ["image"]
    # caption_provider can be wired via env or config in future
    asyncio.run(run_worker_with_client(config, process_image_job))
