"""Worker configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class WorkerConfig:
    """Configuration for the MeshMind worker runtime."""

    agent_id: str | None = field(default_factory=lambda: os.environ.get("MESHMIND_AGENT_ID"))
    control_api_url: str = field(
        default_factory=lambda: os.environ.get("CONTROL_API_URL", "http://localhost:3000")
    )
    agent_name: str = field(
        default_factory=lambda: os.environ.get("MESHMIND_AGENT_NAME", "meshmind-worker")
    )
    capabilities: list[str] = field(default_factory=list)
    heartbeat_interval_secs: float = field(
        default_factory=lambda: float(
            os.environ.get("MESHMIND_HEARTBEAT_INTERVAL_SECS", "30")
        )
    )
    claim_interval_secs: float = field(
        default_factory=lambda: float(
            os.environ.get("MESHMIND_CLAIM_INTERVAL_SECS", "5")
        )
    )

    @classmethod
    def from_env(cls) -> WorkerConfig:
        """Build config from environment variables."""
        capabilities_str = os.environ.get("MESHMIND_AGENT_CAPABILITIES", "filesystem")
        capabilities = [c.strip() for c in capabilities_str.split(",") if c.strip()]
        return cls(
            agent_id=os.environ.get("MESHMIND_AGENT_ID"),
            control_api_url=os.environ.get("CONTROL_API_URL", "http://localhost:3000"),
            agent_name=os.environ.get("MESHMIND_AGENT_NAME", "meshmind-fs-connector"),
            capabilities=capabilities,
            heartbeat_interval_secs=float(
                os.environ.get("MESHMIND_HEARTBEAT_INTERVAL_SECS", "30")
            ),
            claim_interval_secs=float(
                os.environ.get("MESHMIND_CLAIM_INTERVAL_SECS", "5")
            ),
        )
