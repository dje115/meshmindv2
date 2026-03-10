"""CLI entry point for OCR worker."""

from __future__ import annotations

import asyncio
import logging
import os

from meshmind_worker_runtime.config import WorkerConfig
from meshmind_worker_runtime.worker import run_worker_with_client, setup_logging

from .processor import process_ocr_job

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def main() -> None:
    config = WorkerConfig.from_env()
    config.capabilities = ["ocr"]
    asyncio.run(run_worker_with_client(config, process_ocr_job))
