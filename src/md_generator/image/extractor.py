from __future__ import annotations

"""Document Image Extractor & Deduplication Engine.

Phase 2E/Prompt 07 Implementation:
- Detects and extracts embedded images from PDF, PPTX, DOCX, and Markdown documents.
- Extracts image metadata, dimensions, format, and source location.
- Generates deterministic image IDs using document identity, source location, and content hash.
- Multi-occurrence deduplication: identical images across pages/slides are tracked by content hash,
  avoiding duplicate OCR processing while recording all source occurrences.
"""

from dataclasses import dataclass, field
import hashlib
import io
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import zipfile

from PIL import Image

from md_generator.image.adapter import OCRResult
from md_generator.semantic.model.schema import SourceLocation


IMAGE_MARKDOWN_REGEX = re.compile(r"!\[(.*?)\]\((.*?)\)")


@dataclass
class ExtractedImage:
    """Represents an image extracted from a document with full provenance."""
    image_id: str                          # Canonical deterministic ID: img_{sha256(doc_id + loc + hash)[:16]}
    document_id: str                       # Owner document ID
    source_location: SourceLocation        # Page, slide, or section location
    content_hash: str                      # SHA-256 of raw image bytes
    format: str                            # e.g., 'png', 'jpeg', 'webp'
    dimensions: Optional[Tuple[int, int]] = None  # (width, height)
    image_path: str = ""                   # File path or reference URI
    alt_text: str = ""                     # Alt caption or diagram title
    raw_bytes: Optional[bytes] = None      # Raw bytes (kept when loaded in memory)
    ocr_result: Optional[OCRResult] = None # OCR result if processed
    occurrences: List[SourceLocation] = field(default_factory=list) # Additional locations if duplicate
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "document_id": self.document_id,
            "content_hash": self.content_hash,
            "format": self.format,
            "dimensions": list(self.dimensions) if self.dimensions else None,
            "image_path": self.image_path,
            "alt_text": self.alt_text,
            "ocr_text": self.ocr_result.text if self.ocr_result else None,
            "ocr_backend": self.ocr_result.backend if self.ocr_result else None,
            "ocr_confidence": self.ocr_result.confidence if self.ocr_result else None,
            "occurrences_count": len(self.occurrences),
            "metadata": self.metadata,
        }


def canonical_image_id(document_id: str, location_key: str, content_hash: str) -> str:
    """Generates a stable, canonical image ID based on document, location, and content hash."""
    raw = f"{document_id}:{location_key}:{content_hash}".encode("utf-8")
    return f"img_{hashlib.sha256(raw).hexdigest()[:16]}"


class DocumentImageExtractor:
    """Extracts embedded images from documents with content-hash deduplication."""

    def __init__(self, base_asset_dir: Optional[Union[Path, str]] = None) -> None:
        self.base_asset_dir = Path(base_asset_dir) if base_asset_dir else None

    def extract_from_markdown(
        self,
        markdown_content: str,
        document_id: str,
        location_type: str = "generic",
        source_path: str = "",
        page: Optional[int] = None,
        slide: Optional[int] = None,
        section: Optional[str] = None,
    ) -> List[ExtractedImage]:
        """Extracts images referenced in Markdown syntax (![alt](path))."""
        images: List[ExtractedImage] = []
        if not markdown_content:
            return images

        for match in IMAGE_MARKDOWN_REGEX.finditer(markdown_content):
            alt_text = match.group(1).strip()
            img_ref = match.group(2).strip()

            # Attempt to resolve image file on disk
            img_bytes: Optional[bytes] = None
            resolved_path = img_ref
            if self.base_asset_dir:
                cand = self.base_asset_dir / img_ref
                if cand.exists() and cand.is_file():
                    try:
                        img_bytes = cand.read_bytes()
                        resolved_path = str(cand).replace("\\", "/")
                    except Exception:
                        pass

            # Compute content hash
            if img_bytes:
                content_hash = hashlib.sha256(img_bytes).hexdigest()
                format_name, dims = self._inspect_image_bytes(img_bytes)
            else:
                content_hash = hashlib.sha256(img_ref.encode("utf-8")).hexdigest()
                format_name = img_ref.split(".")[-1].lower() if "." in img_ref else "unknown"
                dims = None

            loc_key = f"page_{page}" if page else (f"slide_{slide}" if slide else f"sec_{section or 'root'}")
            img_id = canonical_image_id(document_id, f"{loc_key}:{img_ref}", content_hash)

            # Resolve schema-compliant location_type and domain fields
            effective_loc_type = location_type
            if effective_loc_type == "generic":
                if page is not None:
                    effective_loc_type = "pdf"
                elif slide is not None:
                    effective_loc_type = "pptx"
                elif section is not None:
                    effective_loc_type = "docx"

            loc = SourceLocation(
                location_type=effective_loc_type,
                path=source_path,
                page=page if effective_loc_type == "pdf" else None,
                slide=slide if effective_loc_type == "pptx" else None,
                section=section if effective_loc_type == "docx" else None,
            )

            images.append(
                ExtractedImage(
                    image_id=img_id,
                    document_id=document_id,
                    source_location=loc,
                    content_hash=content_hash,
                    format=format_name,
                    dimensions=dims,
                    image_path=resolved_path,
                    alt_text=alt_text,
                    raw_bytes=img_bytes,
                )
            )

        return self.deduplicate_images(images)

    def extract_from_archive(
        self,
        archive_path: Union[Path, str],
        document_id: str,
        doc_type: str,  # "docx" or "pptx"
    ) -> List[ExtractedImage]:
        """Extracts embedded media images directly from OpenXML archives (DOCX / PPTX)."""
        images: List[ExtractedImage] = []
        path = Path(archive_path)
        if not path.exists() or not path.is_file():
            return images

        try:
            with zipfile.ZipFile(path, "r") as z:
                # In OpenXML, media is located under word/media/ or ppt/media/
                media_prefix = "word/media/" if doc_type == "docx" else "ppt/media/"
                for name in z.namelist():
                    if name.startswith(media_prefix) and not name.endswith("/"):
                        img_bytes = z.read(name)
                        content_hash = hashlib.sha256(img_bytes).hexdigest()
                        format_name, dims = self._inspect_image_bytes(img_bytes)

                        loc_type = "docx" if doc_type == "docx" else "pptx"
                        loc_key = name.split("/")[-1]
                        img_id = canonical_image_id(document_id, loc_key, content_hash)

                        loc = SourceLocation(
                            location_type=loc_type,
                            path=str(path).replace("\\", "/"),
                        )

                        images.append(
                            ExtractedImage(
                                image_id=img_id,
                                document_id=document_id,
                                source_location=loc,
                                content_hash=content_hash,
                                format=format_name,
                                dimensions=dims,
                                image_path=name,
                                alt_text=name.split("/")[-1],
                                raw_bytes=img_bytes,
                            )
                        )
        except Exception:
            pass

        return self.deduplicate_images(images)

    @staticmethod
    def deduplicate_images(images: List[ExtractedImage]) -> List[ExtractedImage]:
        """Deduplicates images with identical content hash while tracking all occurrences."""
        deduped: Dict[str, ExtractedImage] = {}
        for img in images:
            h = img.content_hash
            if h not in deduped:
                deduped[h] = img
            else:
                existing = deduped[h]
                if img.source_location not in existing.occurrences:
                    existing.occurrences.append(img.source_location)
        return list(deduped.values())

    @staticmethod
    def _inspect_image_bytes(raw_bytes: bytes) -> Tuple[str, Optional[Tuple[int, int]]]:
        """Inspects image format and dimensions safely using PIL."""
        try:
            with Image.open(io.BytesIO(raw_bytes)) as img:
                fmt = (img.format or "unknown").lower()
                dims = (img.width, img.height)
                return fmt, dims
        except Exception:
            return "unknown", None
