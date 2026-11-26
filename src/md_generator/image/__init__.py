"""image-to-md: multi-engine OCR to Markdown and advanced image intelligence."""

from __future__ import annotations

from md_generator.image.adapter import (
    OCRResult,
    OCRConfig,
    OCRCache,
    UnifiedOCRAdapter,
)
from md_generator.image.extractor import (
    ExtractedImage,
    DocumentImageExtractor,
    canonical_image_id,
)
from md_generator.image.enricher import (
    OCREnricher,
    EnrichmentResult,
    normalize_ocr_text,
)

__all__ = [
    "OCRResult",
    "OCRConfig",
    "OCRCache",
    "UnifiedOCRAdapter",
    "ExtractedImage",
    "DocumentImageExtractor",
    "canonical_image_id",
    "OCREnricher",
    "EnrichmentResult",
    "normalize_ocr_text",
]
