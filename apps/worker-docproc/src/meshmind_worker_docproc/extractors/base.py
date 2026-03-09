"""Base types for extractors."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..models import NormalizedDocument


Extractor = Callable[[Path, dict], "ExtractionResult"]


class ExtractionResult:
    """Result of extraction - document or structured failure."""

    def __init__(
        self,
        document: NormalizedDocument | None = None,
        failure_reason: str | None = None,
    ) -> None:
        self.document = document
        self.failure_reason = failure_reason

    @property
    def success(self) -> bool:
        return self.document is not None and self.failure_reason is None
