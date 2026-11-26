from __future__ import annotations

"""Citation Manager: Deterministic, Clickable Citation & Link Generation.

Phase 1C/Prompt 04 Implementation:
- Formats deterministic clickable links (#page=N, #slide=N, #section=S, #Lstart-Lend) without fabricating missing locations.
- Extracts and parses citations from generated responses and retrieved contexts.
- Formats inline markers [1], headers, and markdown reference lists.
"""

from dataclasses import dataclass, field, asdict
import re
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class Citation:
    """Canonical citation model representing a verifiable source reference."""
    citation_id: str
    document_id: str
    chunk_id: Optional[str] = None
    source_uri: str = ""
    source_path: str = ""
    location_type: str = "generic"
    page: Optional[int] = None
    slide: Optional[int] = None
    section: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    score: Optional[float] = None
    preview_text: str = ""
    semantic_key: str = ""
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def format_link(self) -> str:
        """Generates a deterministic clickable link or URI without fabricating missing fields."""
        base = self.source_uri or self.source_path or self.document_id

        # Enforce strict non-fabrication: only append fragment if the field is genuinely present
        if self.location_type == "pdf" and self.page is not None:
            return f"{base}#page={self.page}"
        elif self.location_type == "pptx" and self.slide is not None:
            return f"{base}#slide={self.slide}"
        elif self.location_type == "docx" and self.section is not None:
            return f"{base}#section={self.section}"
        elif self.location_type == "code" and self.line_start is not None:
            if self.line_end is not None and self.line_end != self.line_start:
                return f"{base}#L{self.line_start}-L{self.line_end}"
            return f"{base}#L{self.line_start}"
        elif self.page is not None:
            return f"{base}#page={self.page}"
        elif self.slide is not None:
            return f"{base}#slide={self.slide}"
        elif self.line_start is not None:
            if self.line_end is not None and self.line_end != self.line_start:
                return f"{base}#L{self.line_start}-L{self.line_end}"
            return f"{base}#L{self.line_start}"

        return base

    def format_inline(self, index: Optional[int] = None) -> str:
        """Formats inline citation marker, e.g. [1] or [cit_1]."""
        if index is not None:
            return f"[{index}]"
        return f"[{self.citation_id}]"

    def format_header(self) -> str:
        """Formats standard document citation header for prompt injection."""
        loc_str = ""
        link = self.format_link()
        if link:
            loc_str = f" Location: {link} |"
        key_str = f" Key: {self.semantic_key}" if self.semantic_key else ""
        chunk_str = self.chunk_id or ""
        return f"--- [Source: {self.document_id} | Chunk: {chunk_str} |{loc_str}{key_str}] ---"

    def to_dict(self) -> Dict[str, Any]:
        """Converts citation to JSON-serializable dictionary."""
        d = asdict(self)
        d["link"] = self.format_link()
        return d


class CitationManager:
    """Manages creation, formatting, extraction, and validation of citations."""

    def __init__(self, base_url: str = "") -> None:
        self.base_url = base_url.rstrip("/")

    def from_item(self, item: Any, index: Optional[int] = None) -> Citation:
        """Extracts metadata from SemanticChunk, ScoredHybridResult, Document, or dict to build a Citation."""
        citation_id = f"cit_{index}" if index is not None else "cit_0"

        # Check for SemanticChunk
        if hasattr(item, "chunk_id") and hasattr(item, "sanitized_content") and hasattr(item, "document_id"):
            chunk_id = item.chunk_id
            doc_id = item.document_id
            preview = item.sanitized_content[:150].strip() if item.sanitized_content else ""
            meta = item.metadata
            lineage = item.lineage

            source_uri = meta.source_uri if meta else ""
            source_path = meta.source_path if meta else ""

            loc = lineage.location if lineage else None
            loc_type = loc.location_type if loc else "generic"
            page = loc.page if loc else None
            slide = loc.slide if loc else None
            section = loc.section if loc else None
            l_start = loc.line_start if loc else None
            l_end = loc.line_end if loc else None

            return Citation(
                citation_id=citation_id,
                document_id=doc_id,
                chunk_id=chunk_id,
                source_uri=source_uri,
                source_path=source_path,
                location_type=loc_type,
                page=page,
                slide=slide,
                section=section,
                line_start=l_start,
                line_end=l_end,
                score=1.0,
                preview_text=preview,
            )

        # Check for ScoredHybridResult
        if hasattr(item, "chunk_id") and hasattr(item, "hybrid_score") and hasattr(item, "content"):
            chunk_id = item.chunk_id
            meta = dict(getattr(item, "metadata", {}) or {})
            doc_id = meta.get("document_id") or chunk_id
            preview = item.content[:150].strip() if item.content else ""
            score = float(item.hybrid_score)
            loc = meta.get("source_location")

            loc_type = "generic"
            page = None
            slide = None
            section = None
            l_start = None
            l_end = None
            source_path = meta.get("source_path", "")
            source_uri = meta.get("source_uri", "")

            if isinstance(loc, dict):
                loc_type = loc.get("location_type", "generic")
                page = loc.get("page")
                slide = loc.get("slide")
                section = loc.get("section")
                l_start = loc.get("line_start")
                l_end = loc.get("line_end")
                source_path = source_path or loc.get("path", "")
                source_uri = source_uri or loc.get("uri", "")

            # Direct fallback keys from metadata
            page = page if page is not None else meta.get("page")
            slide = slide if slide is not None else meta.get("slide")
            section = section if section is not None else meta.get("section")

            return Citation(
                citation_id=citation_id,
                document_id=doc_id,
                chunk_id=chunk_id,
                source_uri=source_uri,
                source_path=source_path,
                location_type=loc_type,
                page=page,
                slide=slide,
                section=section,
                line_start=l_start,
                line_end=l_end,
                score=score,
                preview_text=preview,
                custom_metadata=meta,
            )

        # Check for LangChain Document or duck-typed Document
        content = getattr(item, "page_content", "") or ""
        meta = dict(getattr(item, "metadata", {}) or {})
        if not content and isinstance(item, dict):
            content = item.get("page_content") or item.get("content") or item.get("sanitized_content") or ""
            meta = dict(item.get("metadata") or {})
            for k in ("chunk_id", "document_id", "score", "page", "slide", "section", "source_location"):
                if k in item and k not in meta:
                    meta[k] = item[k]

        chunk_id = meta.get("chunk_id")
        doc_id = meta.get("document_id") or (chunk_id or "unknown_doc")
        score = meta.get("score")
        if score is not None:
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = None

        loc = meta.get("source_location")
        loc_type = "generic"
        page = None
        slide = None
        section = None
        l_start = None
        l_end = None
        source_path = meta.get("source_path", "")
        source_uri = meta.get("source_uri", "")

        if isinstance(loc, dict):
            loc_type = loc.get("location_type", "generic")
            page = loc.get("page")
            slide = loc.get("slide")
            section = loc.get("section")
            l_start = loc.get("line_start")
            l_end = loc.get("line_end")
            source_path = source_path or loc.get("path", "")
            source_uri = source_uri or loc.get("uri", "")

        page = page if page is not None else meta.get("page")
        slide = slide if slide is not None else meta.get("slide")
        section = section if section is not None else meta.get("section")

        return Citation(
            citation_id=citation_id,
            document_id=str(doc_id),
            chunk_id=str(chunk_id) if chunk_id else None,
            source_uri=source_uri,
            source_path=source_path,
            location_type=loc_type,
            page=page,
            slide=slide,
            section=section,
            line_start=l_start,
            line_end=l_end,
            score=score,
            preview_text=content[:150].strip() if content else "",
            semantic_key=meta.get("semantic_key", ""),
            custom_metadata=meta,
        )

    def format_citations_list(self, citations: List[Citation], style: str = "markdown") -> str:
        """Formats references into a clean deterministic reference list."""
        if not citations:
            return ""

        lines: List[str] = ["### References"]
        for idx, cit in enumerate(citations, start=1):
            link = cit.format_link()
            loc_info = []
            if cit.page is not None:
                loc_info.append(f"Page {cit.page}")
            if cit.slide is not None:
                loc_info.append(f"Slide {cit.slide}")
            if cit.section is not None:
                loc_info.append(f"Section {cit.section}")
            if cit.line_start is not None:
                loc_info.append(f"Lines {cit.line_start}-{cit.line_end}" if cit.line_end else f"Line {cit.line_start}")

            loc_str = f" ({', '.join(loc_info)})" if loc_info else ""
            doc_label = f"Document: `{cit.document_id[:16]}...`" if len(cit.document_id) > 20 else f"Document: `{cit.document_id}`"
            
            if link:
                lines.append(f"[{idx}] {doc_label}{loc_str} — [{link}]({link})")
            else:
                lines.append(f"[{idx}] {doc_label}{loc_str}")

        return "\n".join(lines)

    def extract_citations_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extracts structured citation markers from candidate or generated response text.
        
        Recognizes:
        - Header citations: --- [Source: <doc> | Chunk: <chunk> | Location: <loc> | Key: <key>] ---
        - Source tags: [Source: <doc_id>] or [Source: <doc_id> | Chunk: <chunk_id>]
        - Numbered markers: [1], [2], etc.
        - Document links: [text](<path>#page=N)
        """
        if not text:
            return []

        results: List[Dict[str, Any]] = []

        # Pattern 1: Canonical header format
        header_pattern = re.compile(
            r"---\s*\[Source:\s*(?P<doc_id>[^|\]]+?)\s*\|\s*Chunk:\s*(?P<chunk_id>[^|\]]*?)\s*"
            r"(?:\|\s*Location:\s*(?P<location>[^|\]]*?)\s*)?"
            r"(?:\|\s*Key:\s*(?P<key>[^\]]*?)\s*)?\]\s*---",
            re.MULTILINE
        )
        for m in header_pattern.finditer(text):
            results.append({
                "type": "header",
                "raw": m.group(0),
                "document_id": m.group("doc_id").strip(),
                "chunk_id": m.group("chunk_id").strip() or None,
                "location": (m.group("location") or "").strip() or None,
                "key": (m.group("key") or "").strip() or None,
            })

        # Pattern 2: Short source tag [Source: <doc_id> ... ]
        tag_pattern = re.compile(
            r"\[Source:\s*(?P<doc_id>[^|\]]+?)(?:\s*\|\s*Chunk:\s*(?P<chunk_id>[^|\]]+?))?\]",
            re.IGNORECASE
        )
        for m in tag_pattern.finditer(text):
            # Avoid duplicate if matched as part of header
            if f"--- {m.group(0)}" in text:
                continue
            results.append({
                "type": "tag",
                "raw": m.group(0),
                "document_id": m.group("doc_id").strip(),
                "chunk_id": m.group("chunk_id").strip() if m.group("chunk_id") else None,
            })

        # Pattern 3: Numbered citation markers [1], [2]
        num_pattern = re.compile(r"\[(?P<num>\d+)\]")
        for m in num_pattern.finditer(text):
            results.append({
                "type": "numbered",
                "raw": m.group(0),
                "index": int(m.group("num")),
            })

        # Pattern 4: Markdown link citations [text](url#page=N)
        link_pattern = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<url>[^\)]+)\)")
        for m in link_pattern.finditer(text):
            results.append({
                "type": "link",
                "raw": m.group(0),
                "label": m.group("label"),
                "url": m.group("url"),
            })

        return results
