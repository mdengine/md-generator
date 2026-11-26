from __future__ import annotations

"""OCR Markdown Text Enricher.

Phase 2E/Prompt 07 Implementation:
- Scans Markdown for embedded image references.
- Runs offline OCR on discovered images via UnifiedOCRAdapter with caching.
- Normalizes extracted OCR text and injects structured OCR block below each image tag.
- Preserves native Markdown and source document text without loss.
- Avoids redundant duplication when OCR text is already present in surrounding context.
"""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from md_generator.image.adapter import UnifiedOCRAdapter, OCRResult
from md_generator.image.extractor import DocumentImageExtractor, ExtractedImage


IMAGE_TAG_PATTERN = re.compile(r"(!\[(.*?)\]\((.*?)\))")
ALREADY_ENRICHED_PATTERN = re.compile(r">\s*\*\*Extracted OCR Text\*\*:")


def normalize_ocr_text(text: str) -> str:
    """Cleans up and normalizes OCR text."""
    if not text:
        return ""
    # Strip non-printable ASCII control characters except \n and \t
    cleaned = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    # Normalize multiple blank lines to a single newline
    lines = [line.strip() for line in cleaned.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


@dataclass
class EnrichmentResult:
    """Outcome of Markdown OCR enrichment."""
    original_markdown: str
    enriched_markdown: str
    enriched_images: List[ExtractedImage]
    ocr_operations_count: int
    cached_hits_count: int

    @property
    def has_ocr_content(self) -> bool:
        return any(bool(img.ocr_result and img.ocr_result.text) for img in self.enriched_images)


class OCREnricher:
    """Enriches Markdown documents with normalized OCR text blocks below image tags."""

    def __init__(
        self,
        ocr_adapter: Optional[UnifiedOCRAdapter] = None,
        base_asset_dir: Optional[Union[Path, str]] = None,
        min_ocr_chars: int = 3,
    ) -> None:
        self.ocr_adapter = ocr_adapter or UnifiedOCRAdapter()
        self.base_asset_dir = Path(base_asset_dir) if base_asset_dir else None
        self.min_ocr_chars = min_ocr_chars
        self.image_extractor = DocumentImageExtractor(base_asset_dir=self.base_asset_dir)

    def enrich_markdown(
        self,
        markdown_text: str,
        document_id: str = "doc_default",
        source_path: str = "",
        page: Optional[int] = None,
        slide: Optional[int] = None,
        section: Optional[str] = None,
    ) -> EnrichmentResult:
        """Parses Markdown, runs OCR on referenced images, and injects OCR blocks."""
        if not markdown_text:
            return EnrichmentResult(
                original_markdown="",
                enriched_markdown="",
                enriched_images=[],
                ocr_operations_count=0,
                cached_hits_count=0,
            )

        extracted_images = self.image_extractor.extract_from_markdown(
            markdown_content=markdown_text,
            document_id=document_id,
            source_path=source_path,
            page=page,
            slide=slide,
            section=section,
        )

        ocr_ops = 0
        cache_hits = 0
        img_by_ref: Dict[str, ExtractedImage] = {}

        # Run OCR on all extracted images (deduplicated by content hash)
        for img in extracted_images:
            if img.raw_bytes:
                res = self.ocr_adapter.extract_from_image(img.raw_bytes)
            elif img.image_path and Path(img.image_path).exists():
                res = self.ocr_adapter.extract_from_image(Path(img.image_path))
            else:
                # File not available on disk
                res = OCRResult(text="", backend="None", language="eng")

            img.ocr_result = res
            if res.from_cache:
                cache_hits += 1
            elif res.text:
                ocr_ops += 1

            # Store by image path/ref for lookup
            img_by_ref[img.image_path] = img
            if img.alt_text:
                img_by_ref[img.alt_text] = img

        # Replace image tags in markdown with enriched version
        enriched_lines: List[str] = []
        lines = markdown_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            match = IMAGE_TAG_PATTERN.search(line)

            if match:
                alt = match.group(2).strip()
                ref = match.group(3).strip()
                tag = match.group(1)

                # Check if the next line is already an OCR block
                next_is_ocr = (i + 1 < len(lines)) and ALREADY_ENRICHED_PATTERN.search(lines[i + 1])

                # Find associated image
                matched_img: Optional[ExtractedImage] = None
                for img in extracted_images:
                    if ref in img.image_path or (alt and alt == img.alt_text):
                        matched_img = img
                        break

                if matched_img and matched_img.ocr_result and matched_img.ocr_result.text and not next_is_ocr:
                    clean_ocr = normalize_ocr_text(matched_img.ocr_result.text)
                    if len(clean_ocr) >= self.min_ocr_chars:
                        # Avoid duplicating if the exact text is already right before or after
                        surrounding = (lines[i - 1] if i > 0 else "") + " " + (lines[i + 1] if i + 1 < len(lines) else "")
                        if clean_ocr.lower() not in surrounding.lower():
                            # Format blockquote OCR block
                            ocr_block_lines = [
                                line,
                                "> **Extracted OCR Text**:",
                            ]
                            for ocr_l in clean_ocr.splitlines():
                                ocr_block_lines.append(f"> {ocr_l}")
                            enriched_lines.append("\n".join(ocr_block_lines))
                            i += 1
                            continue

            enriched_lines.append(line)
            i += 1

        enriched_md = "\n".join(enriched_lines)

        return EnrichmentResult(
            original_markdown=markdown_text,
            enriched_markdown=enriched_md,
            enriched_images=extracted_images,
            ocr_operations_count=ocr_ops,
            cached_hits_count=cache_hits,
        )
