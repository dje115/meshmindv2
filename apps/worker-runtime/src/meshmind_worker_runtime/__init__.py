"""MeshMind v2 shared worker framework.

Workers register with control-api, heartbeat, and claim jobs.
"""

from .client import ClaimedJob, ControlPlaneClient, RegisterResponse
from .config import WorkerConfig
from .worker import run_worker, run_worker_with_client, setup_logging

__all__ = [
    "ClaimedJob",
    "ControlPlaneClient",
    "RegisterResponse",
    "WorkerConfig",
    "run_worker",
    "run_worker_with_client",
    "setup_logging",
]
__version__ = "0.1.0"
