"""Image category classification (screenshot, document-photo, photo)."""

from __future__ import annotations

from .models import ImageCategory


def classify_image(
    width: int,
    height: int,
    ocr_text: str,
    ocr_confidence: float,
) -> ImageCategory:
    """Classify image into screenshot, document_photo, or photo.

    Heuristics:
    - Screenshot: common screen resolutions (e.g. 1920x1080, 1366x768), often 16:9 or 4:3.
    - Document photo: significant OCR text with reasonable confidence.
    - Photo: default.
    """
    if width <= 0 or height <= 0:
        return ImageCategory.UNKNOWN

    # Common screenshot resolutions (non-exhaustive)
    common_screen = {
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (1600, 900),
        (2560, 1440),
        (3840, 2160),
        (1024, 768),
        (800, 600),
    }
    size = (width, height)
    if size in common_screen:
        return ImageCategory.SCREENSHOT

    # Document-photo: substantial OCR text
    if len(ocr_text.strip()) > 50 and ocr_confidence >= 0.3:
        return ImageCategory.DOCUMENT_PHOTO

    return ImageCategory.PHOTO
