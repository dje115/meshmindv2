"""Control plane API client."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class RegisterResponse:
    """Response from /api/workers/register."""

    agent_id: str
    token: str
    config_url: str = ""


@dataclass
class ClaimedJob:
    """A job claimed from the control plane."""

    job_id: str
    job_run_id: str
    source_id: str
    source: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    source_item: dict[str, Any] | None = None


class ControlPlaneClient:
    """Async HTTP client for the MeshMind control plane API."""

    def __init__(
        self,
        base_url: str,
        agent_id: str | None = None,
        capabilities: list[str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._agent_id = agent_id
        self._capabilities = capabilities or []
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> ControlPlaneClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    @property
    def agent_id(self) -> str | None:
        """Current agent ID (set after register)."""
        return self._agent_id

    async def register(self, name: str, capabilities: list[str]) -> RegisterResponse:
        """Register with the control plane. Returns agent_id and token."""
        url = f"{self.base_url}/api/workers/register"
        payload = {"name": name, "capabilities": capabilities}
        logger.info("registering", extra={"name": name, "capabilities": capabilities})
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        self._agent_id = data["agent_id"]
        self._capabilities = capabilities
        logger.info("registered", extra={"agent_id": self._agent_id})
        return RegisterResponse(
            agent_id=data["agent_id"],
            token=data.get("token", ""),
            config_url=data.get("config_url", ""),
        )

    async def heartbeat(self) -> dict[str, Any]:
        """Send heartbeat to control plane."""
        if not self._agent_id:
            raise ValueError("must call register before heartbeat")
        url = f"{self.base_url}/api/workers/heartbeat"
        payload = {"agent_id": self._agent_id}
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def claim(self) -> ClaimedJob | None:
        """Claim a queued job. Returns None if no job available (204)."""
        if not self._agent_id:
            raise ValueError("must call register before claim")
        url = f"{self.base_url}/api/workers/jobs/claim"
        payload = {"agent_id": self._agent_id, "capabilities": self._capabilities}
        resp = await self._client.post(url, json=payload)
        if resp.status_code == 204:
            return None
        resp.raise_for_status()
        data = resp.json()
        logger.info(
            "claimed job",
            extra={
                "job_id": data.get("job_id"),
                "job_run_id": data.get("job_run_id"),
            },
        )
        return ClaimedJob(
            job_id=data["job_id"],
            job_run_id=data["job_run_id"],
            source_id=data.get("source_id", ""),
            source=data.get("source", {}),
            config=data.get("config", {}),
            source_item=data.get("source_item"),
        )

    async def progress(
        self,
        job_id: str,
        job_run_id: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Report progress for a job."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        url = f"{self.base_url}/api/workers/jobs/{job_id}/progress"
        payload: dict[str, Any] = {
            "agent_id": self._agent_id,
            "job_run_id": job_run_id,
            "message": message,
        }
        if details:
            payload["details"] = details
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        logger.debug("progress", extra={"job_id": job_id, "message": message})

    async def complete(
        self,
        job_id: str,
        job_run_id: str,
        artifacts: list[Any] | None = None,
    ) -> None:
        """Mark a job as completed."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        url = f"{self.base_url}/api/workers/jobs/{job_id}/complete"
        payload: dict[str, Any] = {
            "agent_id": self._agent_id,
            "job_run_id": job_run_id,
            "artifacts": artifacts or [],
        }
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        logger.info("job completed", extra={"job_id": job_id})

    async def fail(
        self,
        job_id: str,
        job_run_id: str,
        error: str,
    ) -> None:
        """Mark a job as failed."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        url = f"{self.base_url}/api/workers/jobs/{job_id}/fail"
        payload = {
            "agent_id": self._agent_id,
            "job_run_id": job_run_id,
            "error": error,
        }
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        logger.warning("job failed", extra={"job_id": job_id, "error": error})

    async def create_source_items(
        self,
        source_id: str,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Create source items (batch). Each item: { fingerprint, provenance? }."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        url = f"{self.base_url}/api/workers/sources/{source_id}/items"
        payload = {"agent_id": self._agent_id, "items": items}
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])

    async def get_source_item_artifacts(
        self,
        source_item_id: str,
        job_kind: str,
    ) -> dict[str, Any] | None:
        """Fetch artifacts from latest completed job for source item and job kind."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        url = f"{self.base_url}/api/workers/source-items/{source_item_id}/artifacts"
        resp = await self._client.get(url, params={"job_kind": job_kind})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def index_chunks(
        self,
        source_item_id: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Index chunks for keyword search (chunk_index table)."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        url = f"{self.base_url}/api/workers/source-items/{source_item_id}/index-chunks"
        payload = {"agent_id": self._agent_id, "chunks": chunks}
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def create_job(
        self,
        source_id: str,
        source_item_id: str,
        job_kind: str,
    ) -> dict[str, Any]:
        """Create a downstream job (docproc or image)."""
        if not self._agent_id:
            raise ValueError("agent_id required")
        if job_kind not in ("docproc", "image", "ocr", "enrich", "embed"):
            raise ValueError("job_kind must be docproc, image, ocr, enrich, or embed")
        url = f"{self.base_url}/api/workers/jobs"
        payload = {
            "agent_id": self._agent_id,
            "source_id": source_id,
            "source_item_id": source_item_id,
            "job_kind": job_kind,
        }
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()
