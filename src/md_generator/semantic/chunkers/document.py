from __future__ import annotations

"""Contextual & Parent-Child Document Chunker for MDEngine Phase 1A.

Implements structure-preserving, context-aware, parent-child, and overlapping
document chunking for PDF, PPT/PPTX, Word, and Markdown documents.

Invariants & Guarantees:
1. Implements BaseChunker protocol: supports(), chunk_document(), extract_symbols().
2. Stable Chunk Identifiers: Deterministic SHA-256 chunk IDs based on (document_id, semantic_key, content_hash),
   preventing chunk ID invalidation when sibling chunks shift sequence indexes.
3. Strict Schema Compliance: Strictly conforms to SemanticChunk, ChunkLineage, and SourceLocation schemas.
   Validates permitted domain fields per location_type ('pdf' -> page, 'pptx' -> slide, etc.).
4. Hierarchical Parent-Child Linking: Every child chunk maintains its parent_chunk_id and document_id.
5. Sentence-Boundary Overlapping: 15% default overlap preserving sentence, table, and codeblock boundaries.
"""

from dataclasses import dataclass, field
import hashlib
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Tuple

from md_generator.lineage.ids import (
    compute_content_hash,
    generate_chunk_id,
    normalize_source_uri,
)
from md_generator.semantic.chunkers.base import (
    BaseChunker,
    ParseStatus,
    SemanticDiagnostic,
    SymbolExtractionResult,
)
from md_generator.semantic.model.schema import (
    CanonicalMetadata,
    ChunkLineage,
    Entity,
    Relationship,
    SecurityMetadata,
    SemanticChunk,
    SemanticDocument,
    SourceLocation,
)


# Supported source types for contextual document chunking
DOCUMENT_SOURCE_TYPES: Set[str] = {
    "doc.pdf",
    "pdf",
    "doc.ppt",
    "doc.pptx",
    "ppt",
    "pptx",
    "doc.word",
    "docx",
    "doc.markdown",
    "markdown",
    "md",
    "text.plain",
    "generic",
}

# Regex patterns for structural headers
PAGE_PATTERN = re.compile(r"^#{1,3}\s+Page\s+(\d+)", re.IGNORECASE | re.MULTILINE)
SLIDE_PATTERN = re.compile(r"^#{1,3}\s+Slide\s+(\d+)(?::\s*(.*))?", re.IGNORECASE | re.MULTILINE)
SECTION_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
TABLE_BLOCK_PATTERN = re.compile(r"((?:^\|[^\n]+\|(?:\r?\n|$))+)", re.MULTILINE)
IMAGE_REF_PATTERN = re.compile(r"!\[(.*?)\]\((.*?)\)")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def _slugify(text: str) -> str:
    """Create a URL-safe deterministic slug from a section title."""
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", "", text.strip().lower())
    slug = re.sub(r"[\s\-]+", "_", cleaned).strip("_")
    return slug[:48] if slug else "section"


def _estimate_tokens(text: str) -> int:
    """Deterministic token estimation (approx 4 chars per token or whitespace split)."""
    if not text:
        return 0
    return max(len(text) // 4, len(text.split()))


@dataclass
class DocumentChunkerConfig:
    """Configuration options for contextual document chunking."""
    chunk_size: int = 512              # Target token count per child chunk
    min_chunk_size: int = 64           # Minimum token threshold for standalone chunk
    max_chunk_size: int = 1024         # Maximum token threshold before hard sentence split
    overlap_pct: float = 0.15          # Overlap fraction (0.15 = 15%)
    enable_parent_child: bool = True   # Generate parent sections/pages and child paragraphs
    enable_table_extraction: bool = True # Extract distinct table child chunks
    enable_image_ocr_extraction: bool = True # Extract image/OCR child chunks
    preserve_sentences: bool = True    # Always split on sentence boundaries


class ContextualDocumentChunker:
    """Advanced contextual document chunker supporting PDF, PPTX, Word, and Markdown."""

    def __init__(self, config: Optional[DocumentChunkerConfig] = None) -> None:
        self.config = config or DocumentChunkerConfig()

    def supports(self, source_type: str) -> bool:
        """Return True if this chunker handles the given source_type."""
        if not source_type:
            return False
        st = source_type.strip().lower()
        if st in DOCUMENT_SOURCE_TYPES:
            return True
        if st.startswith("doc.") or st.startswith("text."):
            return True
        return False

    def chunk_document(self, document: SemanticDocument) -> List[SemanticChunk]:
        """Parse SemanticDocument into structural, parent-child SemanticChunks."""
        if not isinstance(document, SemanticDocument):
            raise TypeError("document must be an instance of SemanticDocument.")

        content = document.sanitized_content or ""
        doc_id = document.document_id
        if not doc_id:
            raise ValueError("document must have a valid 64-char hex document_id.")

        metadata = document.metadata
        source_type = (metadata.source_type if metadata else "generic").lower()
        source_uri = metadata.source_uri if metadata else ""
        source_path = metadata.source_path if metadata else ""

        # Determine location type for SourceLocation schema compliance
        loc_type = self._resolve_location_type(source_type, source_uri)

        # Step 1: Detect structural units (Pages for PDF, Slides for PPTX, or Sections)
        structural_units = self._parse_structural_units(content, loc_type)

        chunks: List[SemanticChunk] = []
        seq_index = 0

        # Step 2: Generate Document-level Parent Chunk
        doc_chunk_hash = compute_content_hash(content)
        doc_semantic_key = "document:root"
        doc_chunk_id = generate_chunk_id(doc_id, doc_semantic_key, doc_chunk_hash)

        doc_location = self._create_source_location(loc_type, source_uri, source_path)
        doc_lineage = ChunkLineage(
            source_hash=doc_chunk_hash,
            chunk_hash=doc_chunk_hash,
            parent_chunk_id=None,
            sequence_index=seq_index,
            location=doc_location,
        )

        doc_chunk = SemanticChunk(
            schema_version="1.0",
            chunk_id=doc_chunk_id,
            document_id=doc_id,
            sanitized_content=content[:1024] if len(content) > 1024 else content,
            metadata=metadata,
            lineage=doc_lineage,
            security=document.security,
        )
        if self.config.enable_parent_child:
            chunks.append(doc_chunk)
            seq_index += 1

        # Step 3: Process structural units (Pages, Slides, or Major Sections)
        for unit in structural_units:
            unit_title = unit["title"]
            unit_num = unit.get("number")
            unit_content = unit["content"]
            unit_hash = compute_content_hash(unit_content)

            # Build unit semantic key for stable chunk ID
            if loc_type == "pdf" and unit_num is not None:
                unit_semantic_key = f"page:{unit_num}"
            elif loc_type == "pptx" and unit_num is not None:
                unit_semantic_key = f"slide:{unit_num}"
            else:
                unit_semantic_key = f"section:{_slugify(unit_title)}"

            unit_chunk_id = generate_chunk_id(doc_id, unit_semantic_key, unit_hash)
            unit_location = self._create_source_location(
                loc_type, source_uri, source_path, page=unit_num if loc_type == "pdf" else None,
                slide=unit_num if loc_type == "pptx" else None,
                section=unit_title if loc_type == "docx" else None
            )

            unit_lineage = ChunkLineage(
                source_hash=doc_chunk_hash,
                chunk_hash=unit_hash,
                parent_chunk_id=doc_chunk_id if self.config.enable_parent_child else None,
                sequence_index=seq_index,
                location=unit_location,
            )

            parent_unit_chunk = SemanticChunk(
                schema_version="1.0",
                chunk_id=unit_chunk_id,
                document_id=doc_id,
                sanitized_content=unit_content,
                metadata=metadata,
                lineage=unit_lineage,
                security=document.security,
            )
            chunks.append(parent_unit_chunk)
            seq_index += 1

            # Step 4: Extract Child Chunks (Tables, Image OCR, and Overlapping Paragraphs)
            if self.config.enable_parent_child:
                child_chunks = self._generate_child_chunks(
                    parent_chunk=parent_unit_chunk,
                    unit_content=unit_content,
                    unit_semantic_key=unit_semantic_key,
                    unit_location=unit_location,
                    doc_id=doc_id,
                    metadata=metadata,
                    security=document.security,
                    start_seq=seq_index,
                )
                chunks.extend(child_chunks)
                seq_index += len(child_chunks)

        return chunks

    def extract_symbols(self, document: SemanticDocument) -> SymbolExtractionResult:
        """Extract domain Entities, Relationships, and Diagnostics from document structure."""
        content = document.sanitized_content or ""
        doc_id = document.document_id
        metadata = document.metadata
        source_type = (metadata.source_type if metadata else "generic").lower()
        source_uri = metadata.source_uri if metadata else ""
        source_path = metadata.source_path if metadata else ""
        loc_type = self._resolve_location_type(source_type, source_uri)

        entities: List[Entity] = []
        relationships: List[Relationship] = []
        diagnostics: List[SemanticDiagnostic] = []

        doc_entity_id = doc_id[:16]
        doc_entity = Entity(
            entity_id=doc_entity_id,
            entity_type="document",
            name=metadata.source_path.split("/")[-1] if metadata and metadata.source_path else "document",
            qualified_name=f"document:{doc_id[:8]}",
            location=self._create_source_location(loc_type, source_uri, source_path),
        )
        entities.append(doc_entity)

        structural_units = self._parse_structural_units(content, loc_type)
        for unit in structural_units:
            u_num = unit.get("number")
            u_title = unit["title"]

            if loc_type == "pdf" and u_num is not None:
                ent_type = "page"
                ent_name = f"Page {u_num}"
                ent_key = f"page_{u_num}"
                loc = self._create_source_location(loc_type, source_uri, source_path, page=u_num)
            elif loc_type == "pptx" and u_num is not None:
                ent_type = "slide"
                ent_name = f"Slide {u_num}: {u_title}" if u_title else f"Slide {u_num}"
                ent_key = f"slide_{u_num}"
                loc = self._create_source_location(loc_type, source_uri, source_path, slide=u_num)
            else:
                ent_type = "section"
                ent_name = u_title
                ent_key = f"sec_{_slugify(u_title)}"
                loc = self._create_source_location(loc_type, source_uri, source_path, section=u_title if loc_type == "docx" else None)

            raw_eid = f"{doc_entity_id}_{ent_key}"
            unit_eid = hashlib.sha256(raw_eid.encode("utf-8")).hexdigest()[:16]

            unit_entity = Entity(
                entity_id=unit_eid,
                entity_type=ent_type,
                name=ent_name,
                qualified_name=f"{ent_type}:{ent_key}",
                location=loc,
            )
            entities.append(unit_entity)

            # Relationship: Document CONTAINS Page/Slide/Section
            raw_rid = f"rel_contains_{doc_entity_id}_{unit_eid}"
            rel_id = hashlib.sha256(raw_rid.encode("utf-8")).hexdigest()[:16]
            rel = Relationship(
                relationship_id=rel_id,
                source_entity_id=doc_entity_id,
                target_entity_id=unit_eid,
                relationship_type="CONTAINS",
                confidence=1.0,
            )
            relationships.append(rel)

            # Detect images within this unit
            for img_match in IMAGE_REF_PATTERN.finditer(unit["content"]):
                img_alt, img_src = img_match.group(1), img_match.group(2)
                raw_img_id = f"img_{hashlib.sha256(img_src.encode('utf-8')).hexdigest()[:12]}"
                img_eid = hashlib.sha256(f"{doc_entity_id}_{raw_img_id}".encode("utf-8")).hexdigest()[:16]
                img_entity = Entity(
                    entity_id=img_eid,
                    entity_type="image",
                    name=img_alt or img_src.split("/")[-1],
                    qualified_name=f"image:{img_src}",
                    location=loc,
                )
                entities.append(img_entity)

                # Relationship: Page/Slide REFERENCES_IMAGE Image
                raw_rel_img = f"rel_ref_img_{unit_eid}_{img_eid}"
                rel_img_id = hashlib.sha256(raw_rel_img.encode("utf-8")).hexdigest()[:16]
                rel_img = Relationship(
                    relationship_id=rel_img_id,
                    source_entity_id=unit_eid,
                    target_entity_id=img_eid,
                    relationship_type="REFERENCES_IMAGE",
                    confidence=1.0,
                )
                relationships.append(rel_img)

        return SymbolExtractionResult(
            entities=entities,
            relationships=relationships,
            diagnostics=diagnostics,
            parse_status=ParseStatus.CLEAN,
        )

    # -------------------------------------------------------------------------
    # Internal Helpers: Structural Parsing, Overlap & Schema Location Handling
    # -------------------------------------------------------------------------

    def _resolve_location_type(self, source_type: str, source_uri: str) -> str:
        """Resolve valid SourceLocation location_type from source_type and URI."""
        st = (source_type or "").lower()
        uri = (source_uri or "").lower()
        if "pdf" in st or uri.endswith(".pdf"):
            return "pdf"
        if "ppt" in st or uri.endswith(".pptx") or uri.endswith(".ppt"):
            return "pptx"
        if "word" in st or "docx" in st or uri.endswith(".docx") or uri.endswith(".doc"):
            return "docx"
        return "generic"

    def _create_source_location(
        self,
        loc_type: str,
        source_uri: str,
        source_path: str,
        page: Optional[int] = None,
        slide: Optional[int] = None,
        section: Optional[str] = None,
    ) -> SourceLocation:
        """Construct a schema-valid SourceLocation enforcing domain field constraints."""
        norm_uri = normalize_source_uri(source_uri) if source_uri else ""
        norm_path = source_path.replace("\\", "/") if source_path else ""

        if loc_type == "pdf":
            return SourceLocation(
                location_type="pdf",
                uri=norm_uri,
                path=norm_path,
                page=page,
            )
        elif loc_type == "pptx":
            return SourceLocation(
                location_type="pptx",
                uri=norm_uri,
                path=norm_path,
                slide=slide,
            )
        elif loc_type == "docx":
            return SourceLocation(
                location_type="docx",
                uri=norm_uri,
                path=norm_path,
                section=section,
            )
        else:
            return SourceLocation(
                location_type="generic",
                uri=norm_uri,
                path=norm_path,
            )

    def _parse_structural_units(self, content: str, loc_type: str) -> List[Dict[str, Any]]:
        """Deconstruct document content into structural units (Pages, Slides, or Sections)."""
        units: List[Dict[str, Any]] = []

        if loc_type == "pdf" and PAGE_PATTERN.search(content):
            # Split on PDF page headers
            matches = list(PAGE_PATTERN.finditer(content))
            for i, m in enumerate(matches):
                page_num = int(m.group(1))
                start_pos = m.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                page_text = content[start_pos:end_pos].strip()
                units.append({
                    "title": f"Page {page_num}",
                    "number": page_num,
                    "content": page_text,
                })
        elif loc_type == "pptx" and SLIDE_PATTERN.search(content):
            # Split on PPTX slide headers
            matches = list(SLIDE_PATTERN.finditer(content))
            for i, m in enumerate(matches):
                slide_num = int(m.group(1))
                slide_title = m.group(2) or ""
                start_pos = m.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                slide_text = content[start_pos:end_pos].strip()
                units.append({
                    "title": slide_title.strip() if slide_title else f"Slide {slide_num}",
                    "number": slide_num,
                    "content": slide_text,
                })
        else:
            # Markdown / Word / General Text: split on top-level markdown headings (# or ##)
            h_matches = [m for m in SECTION_PATTERN.finditer(content) if len(m.group(1)) <= 2]
            if h_matches:
                for i, m in enumerate(h_matches):
                    sec_title = m.group(2).strip()
                    start_pos = m.start()
                    end_pos = h_matches[i + 1].start() if i + 1 < len(h_matches) else len(content)
                    sec_text = content[start_pos:end_pos].strip()
                    units.append({
                        "title": sec_title,
                        "number": i + 1,
                        "content": sec_text,
                    })
            else:
                # Fallback: single document unit
                units.append({
                    "title": "Document Content",
                    "number": 1,
                    "content": content.strip(),
                })

        return units

    def _generate_child_chunks(
        self,
        parent_chunk: SemanticChunk,
        unit_content: str,
        unit_semantic_key: str,
        unit_location: SourceLocation,
        doc_id: str,
        metadata: Optional[CanonicalMetadata],
        security: Optional[SecurityMetadata],
        start_seq: int,
    ) -> List[SemanticChunk]:
        """Generate fine-grained child chunks: Tables, Image OCR blocks, and Overlapping Paragraphs."""
        child_chunks: List[SemanticChunk] = []
        cur_seq = start_seq

        # 1. Extract Standalone Table Chunks
        if self.config.enable_table_extraction:
            tables = list(TABLE_BLOCK_PATTERN.finditer(unit_content))
            for t_idx, t_match in enumerate(tables):
                table_str = t_match.group(1).strip()
                if table_str.count("\n") >= 2:  # Must have header + divider + at least 1 row
                    tbl_hash = compute_content_hash(table_str)
                    tbl_key = f"{unit_semantic_key}:tbl:{tbl_hash[:12]}"
                    tbl_chunk_id = generate_chunk_id(doc_id, tbl_key, tbl_hash)

                    tbl_lineage = ChunkLineage(
                        source_hash=parent_chunk.lineage.source_hash if parent_chunk.lineage else "",
                        chunk_hash=tbl_hash,
                        parent_chunk_id=parent_chunk.chunk_id,
                        sequence_index=cur_seq,
                        location=unit_location,
                    )
                    child_chunks.append(
                        SemanticChunk(
                            schema_version="1.0",
                            chunk_id=tbl_chunk_id,
                            document_id=doc_id,
                            sanitized_content=table_str,
                            metadata=metadata,
                            lineage=tbl_lineage,
                            security=security,
                        )
                    )
                    cur_seq += 1

        # 2. Extract Image OCR Blocks
        if self.config.enable_image_ocr_extraction:
            # Pattern matching markdown image tags followed by single-line or multi-line extracted OCR text
            ocr_pattern = re.compile(
                r"(!\[(.*?)\]\((.*?)\)(?:\s*(?:>\s*\*\*Extracted OCR Text\*\*:[^\n]*(?:\r?\n\s*>[^\n]*)*))?)",
                re.MULTILINE,
            )
            for img_idx, img_match in enumerate(ocr_pattern.finditer(unit_content)):
                img_block = img_match.group(1).strip()
                if img_block:
                    img_hash = compute_content_hash(img_block)
                    img_key = f"{unit_semantic_key}:img:{img_hash[:12]}"
                    img_chunk_id = generate_chunk_id(doc_id, img_key, img_hash)

                    img_lineage = ChunkLineage(
                        source_hash=parent_chunk.lineage.source_hash if parent_chunk.lineage else "",
                        chunk_hash=img_hash,
                        parent_chunk_id=parent_chunk.chunk_id,
                        sequence_index=cur_seq,
                        location=unit_location,
                    )
                    child_chunks.append(
                        SemanticChunk(
                            schema_version="1.0",
                            chunk_id=img_chunk_id,
                            document_id=doc_id,
                            sanitized_content=img_block,
                            metadata=metadata,
                            lineage=img_lineage,
                            security=security,
                        )
                    )
                    cur_seq += 1

        # 3. Generate Overlapping Paragraph Chunks if content exceeds max_chunk_size
        est_tokens = _estimate_tokens(unit_content)
        if est_tokens > self.config.chunk_size:
            text_chunks = self._split_overlapping_sentences(
                text=unit_content,
                target_tokens=self.config.chunk_size,
                overlap_ratio=self.config.overlap_pct,
            )
            for p_idx, p_text in enumerate(text_chunks):
                p_hash = compute_content_hash(p_text)
                p_key = f"{unit_semantic_key}:p:{p_hash[:12]}"
                p_chunk_id = generate_chunk_id(doc_id, p_key, p_hash)

                p_lineage = ChunkLineage(
                    source_hash=parent_chunk.lineage.source_hash if parent_chunk.lineage else "",
                    chunk_hash=p_hash,
                    parent_chunk_id=parent_chunk.chunk_id,
                    sequence_index=cur_seq,
                    location=unit_location,
                )
                child_chunks.append(
                    SemanticChunk(
                        schema_version="1.0",
                        chunk_id=p_chunk_id,
                        document_id=doc_id,
                        sanitized_content=p_text,
                        metadata=metadata,
                        lineage=p_lineage,
                        security=security,
                    )
                )
                cur_seq += 1

        return child_chunks

    def _split_overlapping_sentences(
        self,
        text: str,
        target_tokens: int,
        overlap_ratio: float,
    ) -> List[str]:
        """Split text into sentence-preserving overlapping windows."""
        paragraphs = text.split("\n\n")
        sentences: List[str] = []
        for para in paragraphs:
            para_clean = para.strip()
            if not para_clean:
                continue
            # Don't split tables or code blocks by sentence
            if para_clean.startswith("|") or para_clean.startswith("```"):
                sentences.append(para_clean)
            else:
                raw_sentences = SENTENCE_SPLIT_PATTERN.split(para_clean)
                sentences.extend([s.strip() for s in raw_sentences if s.strip()])

        if not sentences:
            return [text]

        chunks: List[str] = []
        current_sentences: List[str] = []
        current_token_count = 0
        overlap_tokens = max(int(target_tokens * overlap_ratio), 16)

        for sentence in sentences:
            s_tokens = _estimate_tokens(sentence)
            if current_token_count + s_tokens > target_tokens and current_sentences:
                chunk_str = " ".join(current_sentences)
                chunks.append(chunk_str)

                # Keep overlap sentences from the tail of current window
                overlap_sents: List[str] = []
                acc_overlap = 0
                for s in reversed(current_sentences):
                    acc_overlap += _estimate_tokens(s)
                    overlap_sents.insert(0, s)
                    if acc_overlap >= overlap_tokens:
                        break

                current_sentences = overlap_sents
                current_token_count = sum(_estimate_tokens(s) for s in current_sentences)

            current_sentences.append(sentence)
            current_token_count += s_tokens

        if current_sentences:
            final_str = " ".join(current_sentences)
            if not chunks or final_str != chunks[-1]:
                chunks.append(final_str)

        return chunks if chunks else [text]
