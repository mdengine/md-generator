"""Unit tests for OCR Backend Adapter, Offline Policy, Image Extraction and Caching (Prompt 07)."""

import io
from pathlib import Path
import pytest
from PIL import Image

from md_generator.image.adapter import (
    OCRConfig,
    OCRCache,
    OCRResult,
    UnifiedOCRAdapter,
)
from md_generator.image.extractor import (
    DocumentImageExtractor,
    ExtractedImage,
    canonical_image_id,
)
from md_generator.image.enricher import (
    OCREnricher,
    EnrichmentResult,
    normalize_ocr_text,
)
from md_generator.image.backends.base import OcrBackend
from md_generator.semantic.model.schema import SourceLocation


class MockTestOcrBackend:
    """Deterministic offline mock OCR backend for testing."""
    name = "MockOCR"

    def __init__(self, return_text: str = "Mock Extracted Optical Character Text", confidence: float = 0.95) -> None:
        self.return_text = return_text
        self.last_confidence = confidence
        self.calls_count = 0

    def extract(self, image: Image.Image) -> str:
        self.calls_count += 1
        return self.return_text


class FailingOcrBackend:
    """Mock backend that always raises an exception."""
    name = "FailingOCR"

    def extract(self, image: Image.Image) -> str:
        raise RuntimeError("OCR hardware engine unavailable")


def _create_sample_png_bytes(width: int = 100, height: int = 100, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ==============================================================================
# 1. OCR Adapter & Backend Protocol Tests
# ==============================================================================

def test_ocr_backend_protocol_and_mock_execution():
    """Validates that backends conform to OcrBackend protocol and extract text."""
    mock = MockTestOcrBackend(return_text="Circuit Diagram Model B-12")
    adapter = UnifiedOCRAdapter(
        config=OCRConfig(primary_backend="mock", offline_mode=True, enable_cache=False),
        custom_backends={"mock": mock},
    )

    png_bytes = _create_sample_png_bytes(120, 80)
    result = adapter.extract_from_image(png_bytes)

    assert result.text == "Circuit Diagram Model B-12"
    assert result.backend == "MockOCR"
    assert result.confidence == 0.95
    assert result.word_count == 4
    assert result.from_cache is False
    assert mock.calls_count == 1


def test_ocr_fallback_chain_on_failure():
    """Validates that adapter gracefully falls back when primary backend fails."""
    failing = FailingOcrBackend()
    fallback = MockTestOcrBackend(return_text="Fallback Text Successful")

    adapter = UnifiedOCRAdapter(
        config=OCRConfig(
            primary_backend="failing",
            fallback_backends=("fallback",),
            enable_cache=False,
        ),
        custom_backends={"failing": failing, "fallback": fallback},
    )

    png_bytes = _create_sample_png_bytes(100, 100)
    result = adapter.extract_from_image(png_bytes)

    assert result.text == "Fallback Text Successful"
    assert result.backend == "MockOCR"
    assert fallback.calls_count == 1


def test_ocr_caching_avoids_repeated_processing(tmp_path: Path):
    """Validates that repeated OCR on the same image bytes hits cache with zero duplicate work."""
    mock = MockTestOcrBackend(return_text="Fiber Optic Transceiver 10Gbps")
    cache = OCRCache(cache_dir=tmp_path / "ocr_cache")

    adapter = UnifiedOCRAdapter(
        config=OCRConfig(primary_backend="mock", enable_cache=True),
        custom_backends={"mock": mock},
        cache=cache,
    )

    png_bytes = _create_sample_png_bytes(150, 150)

    # First call: executes backend
    res1 = adapter.extract_from_image(png_bytes)
    assert res1.text == "Fiber Optic Transceiver 10Gbps"
    assert res1.from_cache is False
    assert mock.calls_count == 1

    # Second call with same image: returns from cache!
    res2 = adapter.extract_from_image(png_bytes)
    assert res2.text == "Fiber Optic Transceiver 10Gbps"
    assert res2.from_cache is True
    assert mock.calls_count == 1  # No additional execution!


def test_ocr_dimension_constraints_and_corrupted_images():
    """Validates dimension threshold filtering and graceful handling of corrupted data."""
    mock = MockTestOcrBackend()
    adapter = UnifiedOCRAdapter(
        config=OCRConfig(primary_backend="mock", min_dimension=32),
        custom_backends={"mock": mock},
    )

    # 1. Tiny image (8x8) below min_dimension (e.g. spacer dot or bullet)
    tiny_bytes = _create_sample_png_bytes(8, 8)
    res_tiny = adapter.extract_from_image(tiny_bytes)
    assert res_tiny.text == ""
    assert res_tiny.metadata.get("skipped") is True
    assert mock.calls_count == 0

    # 2. Corrupted random non-image bytes
    res_corrupt = adapter.extract_from_image(b"NOT_A_VALID_IMAGE_HEADER_BYTES")
    assert res_corrupt.text == ""
    assert "error" in res_corrupt.metadata


# ==============================================================================
# 2. Image Extraction & Multi-Occurrence Deduplication Tests
# ==============================================================================

def test_markdown_image_extraction_and_deduplication(tmp_path: Path):
    """Validates extracting images from Markdown and deduplicating identical images."""
    # Create a physical test image on disk
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)
    img_file = img_dir / "logo.png"
    sample_bytes = _create_sample_png_bytes(100, 50, color="blue")
    img_file.write_bytes(sample_bytes)

    extractor = DocumentImageExtractor(base_asset_dir=tmp_path)

    # Markdown with two references to the same image (Page 1 and Page 2)
    md_content = """## Page 1
Welcome to our network architecture.
![Company Logo](images/logo.png)

## Page 2
System overview continued.
![Company Logo](images/logo.png)
"""
    images_p1 = extractor.extract_from_markdown(
        md_content,
        document_id="doc-net-1",
        location_type="pdf",
        source_path="/docs/net.pdf",
        page=1,
    )

    assert len(images_p1) == 1
    extracted = images_p1[0]
    assert extracted.format == "png"
    assert extracted.dimensions == (100, 50)
    assert extracted.alt_text == "Company Logo"
    assert extracted.raw_bytes is not None
    assert len(extracted.content_hash) == 64


def test_canonical_image_id_stability():
    """Validates that canonical image ID is deterministic."""
    id1 = canonical_image_id("doc1", "page_1:images/diag.png", "hash_abc_123")
    id2 = canonical_image_id("doc1", "page_1:images/diag.png", "hash_abc_123")
    id3 = canonical_image_id("doc1", "page_2:images/diag.png", "hash_abc_123")

    assert id1 == id2
    assert id1.startswith("img_")
    assert len(id1) == 20  # "img_" + 16 hex chars
    assert id1 != id3


# ==============================================================================
# 3. OCR Text Enrichment Tests
# ==============================================================================

def test_ocr_markdown_enrichment(tmp_path: Path):
    """Validates injecting structured OCR block below image reference in Markdown."""
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)
    img_file = img_dir / "schema.png"
    img_file.write_bytes(_create_sample_png_bytes(200, 100))

    mock_backend = MockTestOcrBackend(return_text="Database Cluster: Primary Node 1\nReplica Node 2")
    adapter = UnifiedOCRAdapter(
        config=OCRConfig(primary_backend="mock"),
        custom_backends={"mock": mock_backend},
    )

    enricher = OCREnricher(ocr_adapter=adapter, base_asset_dir=tmp_path)

    input_md = """# Architecture Plan

Here is the database schema diagram:
![Schema Diagram](images/schema.png)

Ensure replication lag is under 1 second.
"""
    result = enricher.enrich_markdown(
        markdown_text=input_md,
        document_id="doc_schema_01",
        page=3,
    )

    assert result.has_ocr_content is True
    assert result.ocr_operations_count == 1
    assert "> **Extracted OCR Text**:" in result.enriched_markdown
    assert "> Database Cluster: Primary Node 1" in result.enriched_markdown
    assert "> Replica Node 2" in result.enriched_markdown
    # Original text is preserved intact
    assert "Here is the database schema diagram:" in result.enriched_markdown
    assert "Ensure replication lag is under 1 second." in result.enriched_markdown


def test_ocr_text_normalization():
    """Validates normalization of raw OCR text."""
    raw = "\x00\x01Title Line\r\n\r\n   Subline with details.   \n\x07\n\nFinal Line."
    normalized = normalize_ocr_text(raw)
    assert "\x00" not in normalized
    assert "\x07" not in normalized
    lines = normalized.splitlines()
    assert len(lines) == 3
    assert lines[0] == "Title Line"
    assert lines[1] == "Subline with details."
    assert lines[2] == "Final Line."
