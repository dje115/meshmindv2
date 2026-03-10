"""Optional pluggable caption/description model interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class CaptionProvider(ABC):
    """Abstract interface for image caption/description generation.

    Implementations may use local LLMs (e.g. Ollama), CLIP, or other models.
    """

    @abstractmethod
    def caption(self, image_path: Path, metadata: dict[str, Any] | None = None) -> str | None:
        """Generate caption/description for an image. Returns None if unavailable."""
        ...
