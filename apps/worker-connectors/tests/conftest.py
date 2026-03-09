"""Pytest fixtures for connector tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_folder():
    """Create a temporary folder, yield path, clean up after."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
