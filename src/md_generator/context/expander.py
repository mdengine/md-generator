from __future__ import annotations

"""Context Expander: Parent-Child, Sibling, and Associated Node Expansion.

Phase 1C/Prompt 04 Implementation:
- Implements Small-to-Big contextual retrieval: expands granular child chunks (paragraphs, tables)
  into parent chunks (pages, slides, sections) for richer LLM grounding context.
- Prevents duplicated parent chunks by deduplicating and inheriting the maximum child similarity score.
- Sibling and adjacent node expansion for narrative flow preservation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union


class ParentExpansionMode(str, Enum):
    """Strategy for handling child-to-parent chunk expansion."""
    REPLACE = "replace"  # Standard Small-to-Big: replace child with parent chunk
    APPEND = "append"    # Keep child chunk and append parent chunk
    ENRICH = "enrich"    # Keep child chunk and inject parent content into metadata


@dataclass
class ContextExpanderConfig:
    """Configuration for context expansion."""
    expand_parent: bool = True
    parent_mode: ParentExpansionMode = ParentExpansionMode.REPLACE
    expand_children: bool = False
    expand_siblings: bool = False
    max_siblings_per_chunk: int = 1
    max_total_chunks: int = 50
    preserve_child_scores: bool = True


def _extract_parent_id(item: Any) -> Optional[str]:
    """Extracts parent_chunk_id from item across SemanticChunk, ScoredHybridResult, Document, or dict."""
    if hasattr(item, "lineage") and getattr(item.lineage, "parent_chunk_id", None):
        return item.lineage.parent_chunk_id

    meta = getattr(item, "metadata", None)
    if isinstance(meta, dict) and meta.get("parent_chunk_id"):
        return str(meta["parent_chunk_id"])

    if isinstance(item, dict):
        if item.get("parent_chunk_id"):
            return str(item["parent_chunk_id"])
        meta = item.get("metadata")
        if isinstance(meta, dict) and meta.get("parent_chunk_id"):
            return str(meta["parent_chunk_id"])

    return None


def _extract_chunk_id(item: Any) -> Optional[str]:
    """Extracts chunk_id from item."""
    if hasattr(item, "chunk_id"):
        return str(item.chunk_id)
    meta = getattr(item, "metadata", None)
    if isinstance(meta, dict) and meta.get("chunk_id"):
        return str(meta["chunk_id"])
    if isinstance(item, dict):
        if item.get("chunk_id"):
            return str(item["chunk_id"])
        meta = item.get("metadata")
        if isinstance(meta, dict) and meta.get("chunk_id"):
            return str(meta["chunk_id"])
    return None


def _extract_score(item: Any) -> float:
    """Extracts relevance score from item."""
    if hasattr(item, "hybrid_score"):
        return float(item.hybrid_score)
    meta = getattr(item, "metadata", None)
    if isinstance(meta, dict) and "score" in meta:
        try:
            return float(meta["score"])
        except (ValueError, TypeError):
            pass
    if isinstance(item, dict):
        if "score" in item:
            try:
                return float(item["score"])
            except (ValueError, TypeError):
                pass
        meta = item.get("metadata")
        if isinstance(meta, dict) and "score" in meta:
            try:
                return float(meta["score"])
            except (ValueError, TypeError):
                pass
    return 1.0


def _resolve_chunk_from_store(store: Any, chunk_id: str) -> Optional[Any]:
    """Retrieves a chunk from store supporting dict, callable, or object interfaces."""
    if store is None or not chunk_id:
        return None
    if callable(store):
        return store(chunk_id)
    if isinstance(store, dict):
        return store.get(chunk_id)
    if hasattr(store, "get_chunk"):
        return store.get_chunk(chunk_id)
    if hasattr(store, "get"):
        return store.get(chunk_id)
    return None


class ContextExpander:
    """Expands retrieved candidates with parent, sibling, or associated context."""

    def __init__(
        self,
        chunk_store: Optional[Union[Dict[str, Any], Callable[[str], Optional[Any]], Any]] = None,
        config: Optional[ContextExpanderConfig] = None,
    ) -> None:
        self.chunk_store = chunk_store
        self.config = config or ContextExpanderConfig()

    def expand(
        self,
        retrieved_items: List[Any],
        chunk_store: Optional[Any] = None,
    ) -> List[Any]:
        """Expands retrieved items according to configured parent/sibling/child policies."""
        if not retrieved_items:
            return []

        active_store = chunk_store if chunk_store is not None else self.chunk_store
        if active_store is None:
            # Cannot expand without a chunk store, return items unchanged
            return list(retrieved_items)

        config = self.config
        expanded_list: List[Any] = []
        # Key: chunk_id -> item
        seen_chunks: Dict[str, Any] = {}
        # Parent mapping for REPLACE deduplication: parent_id -> (parent_item, max_score)
        parent_map: Dict[str, Tuple[Any, float]] = {}

        for item in retrieved_items:
            chunk_id = _extract_chunk_id(item)
            parent_id = _extract_parent_id(item)
            child_score = _extract_score(item)

            if config.expand_parent and parent_id:
                # Small-to-big expansion
                parent_chunk = _resolve_chunk_from_store(active_store, parent_id)
                if parent_chunk is not None:
                    if config.parent_mode == ParentExpansionMode.REPLACE:
                        if parent_id in parent_map:
                            # Update existing parent with higher score if applicable
                            existing_p, existing_score = parent_map[parent_id]
                            new_score = max(existing_score, child_score)
                            parent_map[parent_id] = (existing_p, new_score)
                        else:
                            parent_map[parent_id] = (parent_chunk, child_score)
                        continue

                    elif config.parent_mode == ParentExpansionMode.APPEND:
                        if chunk_id:
                            seen_chunks[chunk_id] = item
                        if parent_id not in seen_chunks:
                            # Mark parent with metadata about child
                            seen_chunks[parent_id] = parent_chunk
                        continue

                    elif config.parent_mode == ParentExpansionMode.ENRICH:
                        # Attach parent content into child's metadata
                        if isinstance(parent_chunk, dict):
                            parent_content = (
                                parent_chunk.get("sanitized_content")
                                or parent_chunk.get("page_content")
                                or parent_chunk.get("content")
                                or ""
                            )
                        else:
                            parent_content = (
                                getattr(parent_chunk, "sanitized_content", None)
                                or getattr(parent_chunk, "page_content", None)
                                or getattr(parent_chunk, "content", "")
                            )
                        if hasattr(item, "metadata") and isinstance(item.metadata, dict):
                            item.metadata["parent_content"] = parent_content
                        elif isinstance(item, dict):
                            if "metadata" not in item:
                                item["metadata"] = {}
                            item["metadata"]["parent_content"] = parent_content
                        if chunk_id:
                            seen_chunks[chunk_id] = item
                        continue

            # Fallback / non-parent item
            if chunk_id:
                seen_chunks[chunk_id] = item
            else:
                expanded_list.append(item)

        # Build output based on mode
        if config.expand_parent and config.parent_mode == ParentExpansionMode.REPLACE:
            for pid, (p_item, inherited_score) in parent_map.items():
                # Inject inherited score into parent metadata if configured
                if config.preserve_child_scores:
                    if hasattr(p_item, "metadata") and isinstance(p_item.metadata, dict):
                        p_item.metadata["score"] = inherited_score
                    elif hasattr(p_item, "hybrid_score"):
                        p_item.hybrid_score = inherited_score
                    elif isinstance(p_item, dict):
                        if "metadata" not in p_item:
                            p_item["metadata"] = {}
                        p_item["metadata"]["score"] = inherited_score

                seen_chunks[pid] = p_item

        # Assemble deduplicated list
        final_items = list(seen_chunks.values()) + expanded_list

        # Sibling expansion if configured
        if config.expand_siblings:
            sibling_items: List[Any] = []
            for item in list(final_items):
                cid = _extract_chunk_id(item)
                # Check for sibling_chunk_ids in metadata
                meta = getattr(item, "metadata", {}) or {}
                sibling_ids = meta.get("sibling_chunk_ids", [])
                for sid in sibling_ids[:config.max_siblings_per_chunk]:
                    if sid and sid not in seen_chunks:
                        s_chunk = _resolve_chunk_from_store(active_store, sid)
                        if s_chunk is not None:
                            seen_chunks[sid] = s_chunk
                            sibling_items.append(s_chunk)
            final_items.extend(sibling_items)

        # Enforce max limit
        return final_items[:config.max_total_chunks]
