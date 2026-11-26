from __future__ import annotations

"""Context Manager: Orchestrated Context Assembly & Prompt Synthesis.

Phase 1C/Prompt 04 Implementation:
- Reuses PromptContextBuilder for deterministic 6-level sorting, deduplication, and token budgeting.
- Reuses GraphContextAdapter for graph path traversal enrichment.
- Integrates ContextExpander (Small-to-Big retrieval) and CitationManager (verifiable links).
- Enforces strict multi-tenant boundary checks and document access controls.
- Treats retrieved content as untrusted data with prompt injection delimiter neutralization.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Callable, Dict, List, Optional, Set, Union

from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.context.citation import Citation, CitationManager
from md_generator.context.expander import ContextExpander, ContextExpanderConfig
from md_generator.context.validator import EvidenceValidationResult, EvidenceValidator
from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.graph.hybrid.context import GraphContextAdapter
from md_generator.graph.model import KnowledgeGraph, _validate_tenant_id


# Common prompt injection delimiter sequences neutralized with zero-width spaces (\u200b)
PROMPT_INJECTION_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"<\|im_start\|>", re.IGNORECASE), "<|\u200bim_start|>"),
    (re.compile(r"<\|im_end\|>", re.IGNORECASE), "<|\u200bim_end|>"),
    (re.compile(r"<<SYS>>", re.IGNORECASE), "<\u200b<SYS>\u200b>"),
    (re.compile(r"<</SYS>>", re.IGNORECASE), "<\u200b</SYS>\u200b>"),
    (re.compile(r"\[INST\]", re.IGNORECASE), "[\u200bINST\u200b]"),
    (re.compile(r"\[/INST\]", re.IGNORECASE), "[\u200b/INST\u200b]"),
    (re.compile(r"<system>", re.IGNORECASE), "<\u200bsystem\u200b>"),
    (re.compile(r"</system>", re.IGNORECASE), "<\u200b/system\u200b>"),
    (re.compile(r"###\s*System:", re.IGNORECASE), "###\u200b System:"),
    (re.compile(r"###\s*Instruction:", re.IGNORECASE), "###\u200b Instruction:"),
]


def sanitize_untrusted_text(text: str) -> str:
    """Neutralizes LLM system-prompt control tokens and injection markers in retrieved text."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in PROMPT_INJECTION_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


@dataclass
class _ContextDocument:
    """Standardized document representation compliant with PromptContextBuilder."""
    page_content: str
    metadata: Dict[str, Any]
    original_item: Optional[Any] = None

    @property
    def chunk_id(self) -> str:
        return str(self.metadata.get("chunk_id", ""))

    @property
    def document_id(self) -> str:
        return str(self.metadata.get("document_id", ""))


def to_document_like(item: Any, sanitize: bool = True) -> _ContextDocument:
    """Converts SemanticChunk, ScoredHybridResult, Document, or dict into a standardized document."""
    raw_content = ""
    metadata: Dict[str, Any] = {}

    # 1. SemanticChunk
    if hasattr(item, "sanitized_content") and hasattr(item, "chunk_id"):
        raw_content = item.sanitized_content or ""
        metadata["chunk_id"] = item.chunk_id
        metadata["document_id"] = item.document_id
        metadata["score"] = 1.0

        if item.metadata:
            metadata["source_uri"] = item.metadata.source_uri
            metadata["source_path"] = item.metadata.source_path
            metadata["security_classification"] = item.metadata.security_classification

        if item.lineage:
            if item.lineage.parent_chunk_id:
                metadata["parent_chunk_id"] = item.lineage.parent_chunk_id
            if item.lineage.location:
                loc = item.lineage.location
                metadata["source_location"] = loc.to_dict()
                metadata["location_type"] = loc.location_type
                if loc.page is not None:
                    metadata["page"] = loc.page
                if loc.slide is not None:
                    metadata["slide"] = loc.slide
                if loc.section is not None:
                    metadata["section"] = loc.section

    # 2. ScoredHybridResult
    elif hasattr(item, "content") and hasattr(item, "hybrid_score"):
        raw_content = item.content or ""
        metadata = dict(getattr(item, "metadata", {}) or {})
        metadata["chunk_id"] = item.chunk_id
        metadata["tenant_id"] = item.tenant_id
        metadata["score"] = float(item.hybrid_score)
        metadata["vector_score"] = float(item.vector_score)
        metadata["graph_score"] = float(item.graph_score)
        metadata["provenance"] = item.provenance
        if item.graph_paths:
            metadata["graph_paths"] = [p.to_dict() for p in item.graph_paths]

    # 3. LangChain Document or duck-typed object
    elif hasattr(item, "page_content"):
        raw_content = item.page_content or ""
        metadata = dict(getattr(item, "metadata", {}) or {})
        if "score" not in metadata:
            metadata["score"] = 1.0
        else:
            try:
                metadata["score"] = float(metadata["score"])
            except (ValueError, TypeError):
                metadata["score"] = 1.0

    # 4. Dictionary
    elif isinstance(item, dict):
        raw_content = (
            item.get("page_content")
            or item.get("content")
            or item.get("sanitized_content")
            or ""
        )
        metadata = dict(item.get("metadata") or {})
        for k in (
            "chunk_id", "document_id", "score", "tenant_id", "parent_chunk_id",
            "source_location", "page", "slide", "section", "source_path", "source_uri"
        ):
            if k in item and k not in metadata:
                metadata[k] = item[k]
        if "score" in metadata:
            try:
                metadata["score"] = float(metadata["score"])
            except (ValueError, TypeError):
                metadata["score"] = 1.0
        else:
            metadata["score"] = 1.0

    content = sanitize_untrusted_text(raw_content) if sanitize else raw_content
    return _ContextDocument(page_content=content, metadata=metadata, original_item=item)


@dataclass
class AssembledContext:
    """Synthesized prompt context result with full lineage, citations, and budgeting info."""
    context_text: str
    included_chunks: List[Any]
    excluded_chunks: List[Any]
    citations: List[Citation]
    token_count: int
    max_tokens: int
    tenant_id: str
    has_graph_context: bool = False
    is_truncated: bool = False
    references_text: str = ""


class ContextManager:
    """Enterprise context assembly manager combining prompt synthesis, expansion, and citations."""

    def __init__(
        self,
        context_builder: Optional[PromptContextBuilder] = None,
        graph_adapter: Optional[GraphContextAdapter] = None,
        expander: Optional[ContextExpander] = None,
        citation_manager: Optional[CitationManager] = None,
        validator: Optional[EvidenceValidator] = None,
        max_tokens: int = 4000,
        sanitize_untrusted: bool = True,
        include_citations: bool = True,
    ) -> None:
        self.context_builder = context_builder or PromptContextBuilder(
            max_tokens=max_tokens,
            include_citations=include_citations,
        )
        self.graph_adapter = graph_adapter or GraphContextAdapter(
            context_builder=self.context_builder,
        )
        self.expander = expander or ContextExpander()
        self.citation_manager = citation_manager or CitationManager()
        self.validator = validator or EvidenceValidator(
            citation_manager=self.citation_manager,
        )
        self.max_tokens = max_tokens
        self.sanitize_untrusted = sanitize_untrusted
        self.include_citations = include_citations

    def assemble_context(
        self,
        retrieved_items: List[Any],
        tenant_id: str,
        allowed_document_ids: Optional[Set[str]] = None,
        subgraph: Optional[KnowledgeGraph] = None,
        max_tokens: Optional[int] = None,
        expand_context: bool = True,
        chunk_store: Optional[Any] = None,
        append_references: bool = False,
    ) -> AssembledContext:
        """Assembles deterministic, token-budgeted prompt context from retrieval candidates."""
        clean_tenant = _validate_tenant_id(tenant_id, "ContextManager.tenant_id")
        effective_max_tokens = max_tokens or self.max_tokens

        # Step 1: Multi-tenant boundary validation
        for item in retrieved_items:
            item_tenant = None
            if hasattr(item, "tenant_id"):
                item_tenant = item.tenant_id
            elif hasattr(item, "metadata") and isinstance(item.metadata, dict):
                item_tenant = item.metadata.get("tenant_id")
            elif isinstance(item, dict):
                item_tenant = item.get("tenant_id") or (
                    item.get("metadata", {}).get("tenant_id")
                    if isinstance(item.get("metadata"), dict)
                    else None
                )

            if item_tenant and str(item_tenant).strip() != clean_tenant:
                raise TenantBoundaryError(
                    f"Candidate chunk tenant '{item_tenant}' violates requester tenant boundary '{clean_tenant}'."
                )

        # Step 2: Document access filtering
        filtered_items = []
        for item in retrieved_items:
            doc_id = None
            if hasattr(item, "document_id"):
                doc_id = item.document_id
            elif hasattr(item, "metadata") and isinstance(item.metadata, dict):
                doc_id = item.metadata.get("document_id")
            elif isinstance(item, dict):
                doc_id = item.get("document_id") or (
                    item.get("metadata", {}).get("document_id")
                    if isinstance(item.get("metadata"), dict)
                    else None
                )

            if allowed_document_ids is not None and doc_id:
                if str(doc_id) not in allowed_document_ids:
                    continue
            filtered_items.append(item)

        # Empty candidate handling
        if not filtered_items:
            return AssembledContext(
                context_text="",
                included_chunks=[],
                excluded_chunks=[],
                citations=[],
                token_count=0,
                max_tokens=effective_max_tokens,
                tenant_id=clean_tenant,
                has_graph_context=False,
                is_truncated=False,
            )

        # Step 3: Context expansion (Small-to-Big)
        working_items = filtered_items
        if expand_context and self.expander:
            working_items = self.expander.expand(working_items, chunk_store=chunk_store)

        # Step 4: Convert to standardized document-like objects
        doc_items = [
            to_document_like(item, sanitize=self.sanitize_untrusted)
            for item in working_items
        ]

        # Step 5: Graph enrichment (if graph paths or subgraph present)
        has_graph = False
        has_paths = any(d.metadata.get("graph_paths") for d in doc_items)
        if (subgraph is not None or has_paths) and self.graph_adapter:
            doc_items = self.graph_adapter.augment_documents(doc_items, subgraph=subgraph)
            has_graph = True

        # Step 6: Deduplication & 6-level deterministic ordering
        deduped = self.context_builder.deduplicate_documents(doc_items)
        ordered = self.context_builder.order_documents(deduped)

        # Step 7: Token budgeting
        accumulated_sections: List[str] = []
        included_chunks: List[Any] = []
        excluded_chunks: List[Any] = []
        current_tokens = 0
        is_truncated = False

        for doc in ordered:
            content = getattr(doc, "page_content", "") or ""
            meta = getattr(doc, "metadata", {}) or {}

            section_parts: List[str] = []
            if self.include_citations:
                cit_header = self.citation_manager.from_item(doc).format_header()
                section_parts.append(cit_header)
            section_parts.append(content)
            section_str = "\n".join(section_parts)

            section_tokens = self.context_builder._safe_estimate_tokens(section_str)

            if current_tokens + section_tokens <= effective_max_tokens:
                accumulated_sections.append(section_str)
                included_chunks.append(getattr(doc, "original_item", doc))
                current_tokens += section_tokens
            else:
                excluded_chunks.append(getattr(doc, "original_item", doc))
                is_truncated = True

        context_text = "\n\n".join(accumulated_sections)

        # Step 8: Build citations for included chunks
        citations = [
            self.citation_manager.from_item(chunk, index=i + 1)
            for i, chunk in enumerate(included_chunks)
        ]

        references_text = ""
        if append_references and citations:
            references_text = self.citation_manager.format_citations_list(citations)
            if context_text:
                context_text = f"{context_text}\n\n{references_text}"
            else:
                context_text = references_text

        return AssembledContext(
            context_text=context_text,
            included_chunks=included_chunks,
            excluded_chunks=excluded_chunks,
            citations=citations,
            token_count=current_tokens,
            max_tokens=effective_max_tokens,
            tenant_id=clean_tenant,
            has_graph_context=has_graph,
            is_truncated=is_truncated,
            references_text=references_text,
        )

    def validate_evidence(
        self,
        response_text: str,
        context_or_items: Union[AssembledContext, List[Any]],
    ) -> EvidenceValidationResult:
        """Validates generated response grounding against assembled context or evidence chunks."""
        if isinstance(context_or_items, AssembledContext):
            evidence_items = context_or_items.included_chunks
        else:
            evidence_items = context_or_items
        return self.validator.validate(response_text, evidence_items)
