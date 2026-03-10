"""Image classification tests."""

from __future__ import annotations

import pytest

from meshmind_worker_image.classifier import classify_image
from meshmind_worker_image.models import ImageCategory


def test_screenshot_1920x1080() -> None:
    """1920x1080 is classified as screenshot."""
    cat = classify_image(1920, 1080, "", 0.0)
    assert cat == ImageCategory.SCREENSHOT


def test_document_photo_ocr() -> None:
    """Image with substantial OCR text -> document_photo (non-screen resolution)."""
    text = "This is a scanned document with many words for testing " * 2
    # Use non-screen resolution so we hit document_photo path
    cat = classify_image(1100, 850, text, 0.7)
    assert cat == ImageCategory.DOCUMENT_PHOTO


def test_photo_default() -> None:
    """Generic dimensions and little OCR -> photo (640x480 is not in common_screen)."""
    cat = classify_image(640, 480, "x", 0.1)
    assert cat == ImageCategory.PHOTO


def test_unknown_zero_size() -> None:
    """Zero size -> unknown."""
    cat = classify_image(0, 0, "", 0.0)
    assert cat == ImageCategory.UNKNOWN
