"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
