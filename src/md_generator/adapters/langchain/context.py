"""PromptContextBuilder for deterministic token-bounded context prompt synthesis."""

import math
import json
import hashlib
import re
from typing import List, Optional, Callable, Dict, Any, Tuple
from dataclasses import is_dataclass, asdict


def _normalize_value(val: Any) -> Any:
    """Recursively normalizes a metadata value into a canonical JSON-serializable structure.
    
    Invariants:
    - Preserves type distinctions (bool vs int, int vs float, None vs str).
    - Sorts dictionary keys recursively regardless of insertion order.
    - Recursively processes lists, tuples, sets, and dataclasses.
    - Strips memory addresses and unstable object pointers from custom representations.
    """
    if val is None:
        return None
    if isinstance(val, bool):
        # Must check bool before int because bool is a subclass of int in Python
        return val
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return f"__float_{val}__"
        return val
    if isinstance(val, str):
        return val
    if is_dataclass(val) and not isinstance(val, type):
        return _normalize_value(asdict(val))
    if isinstance(val, dict):
        return {
            str(k): _normalize_value(v)
            for k, v in sorted(val.items(), key=lambda item: str(item[0]))
        }
    if isinstance(val, (list, tuple)):
        return [_normalize_value(item) for item in val]
    if isinstance(val, set):
        normalized_items = [_normalize_value(item) for item in val]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
        )
    # Unsupported / custom objects: sanitize representation removing memory addresses
    raw_repr = repr(val)
    clean_repr = re.sub(r' at 0x[0-9a-fA-F]+>', '>', raw_repr)
    return f"{type(val).__name__}:{clean_repr}"


def canonical_document_fingerprint(doc: Any) -> str:
    """Computes a deterministic standard-library fingerprint for a document's content and metadata."""
    content = getattr(doc, "page_content", "") or ""
    meta = getattr(doc, "metadata", {}) or {}
    norm_meta = _normalize_value(meta)
    canonical_json = json.dumps(
        norm_meta,
        sort_keys=True,
        ensure_ascii=True,
        separators=(',', ':')
    )
    payload = content.encode("utf-8") + b"|" + canonical_json.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def extract_and_validate_score(doc: Any) -> float:
    """Extracts and validates relevance score from document metadata.
    
    Rejects non-numeric values, booleans, NaN, +/-Inf, and conversion overflows with explicit ValueError.
    """
    meta = getattr(doc, "metadata", {}) or {}
    val = meta.get("score", 0.0)
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(
            f"Document metadata 'score' must be a numeric float or int. Got: {type(val).__name__} ({val})"
        )
    try:
        f_val = float(val)
    except OverflowError as e:
        raise ValueError(f"Document metadata 'score' exceeds floating point range (overflow): {e}") from e

    if math.isnan(f_val) or math.isinf(f_val):
        raise ValueError(f"Document metadata 'score' must be a finite float. Got: {f_val}")
    return f_val


def estimate_token_count(text: str) -> int:
    """Deterministic standard-library token estimator.
    
    Combines character ratio (approx 4 chars/token) with word token heuristic:
    max(math.ceil(len(text) / 4), len(text.split()))
    """
    if not text:
        return 0
    return max(math.ceil(len(text) / 4), len(text.split()))


class PromptContextBuilder:
    """Synthesizes retrieved LangChain Documents into deterministic, token-bounded prompt contexts."""

    def __init__(
        self,
        max_tokens: int = 4000,
        token_estimator: Optional[Callable[[str], int]] = None,
        include_citations: bool = True,
    ):
        if not isinstance(max_tokens, int) or max_tokens < 1:
            raise ValueError(f"max_tokens must be a positive integer >= 1. Got: {max_tokens}")
        self.max_tokens = max_tokens
        self.token_estimator = token_estimator or estimate_token_count
        self.include_citations = include_citations

    def _safe_estimate_tokens(self, text: str) -> int:
        """Invokes token estimator and validates return type is a non-negative integer."""
        val = self.token_estimator(text)
        if isinstance(val, bool) or not isinstance(val, int) or val < 0:
            raise ValueError(f"token_estimator must return a non-negative integer. Got: {val}")
        return val

    def _format_citation(self, metadata: Dict[str, Any]) -> str:
        doc_id = metadata.get("document_id") or ""
        chunk_id = metadata.get("chunk_id") or ""
        key = metadata.get("semantic_key") or ""
        loc = metadata.get("source_location")
        loc_str = ""
        if isinstance(loc, dict):
            path = loc.get("path") or loc.get("uri") or ""
            l_start = loc.get("line_start")
            l_end = loc.get("line_end")
            if l_start is not None and l_end is not None:
                loc_str = f" Location: {path}:{l_start}-{l_end} |"
            elif l_start is not None:
                loc_str = f" Location: {path}:{l_start} |"
            elif path:
                loc_str = f" Location: {path} |"

        return f"--- [Source: {doc_id} | Chunk: {chunk_id} |{loc_str} Key: {key}] ---"

    def deduplicate_documents(self, documents: List[Any]) -> List[Any]:
        """Deduplicates documents retaining strictly the occurrence with highest relevance score.
        
        Uses collision-safe tuple keys:
        - Primary: ("chunk", chunk_id) when chunk_id is present and non-empty
        - Secondary: ("document_semantic", doc_id, sem_key) when doc_id and sem_key are present and non-empty
        - Unkeyed Preservation: Documents lacking reliable identity are preserved individually.
        - Deterministic Tie-Breaker: When candidate scores are equal, the candidate with the lexicographically
          smaller canonical_document_fingerprint() is retained, guaranteeing order-independent output.
        """
        best_by_key: Dict[Tuple[str, ...], Any] = {}
        unkeyed_documents: List[Any] = []

        for doc in documents:
            meta = getattr(doc, "metadata", {}) or {}
            chunk_id = meta.get("chunk_id")
            doc_id = meta.get("document_id")
            sem_key = meta.get("semantic_key")

            if chunk_id and isinstance(chunk_id, str) and chunk_id.strip():
                dedup_key: Optional[Tuple[str, ...]] = ("chunk", chunk_id.strip())
            elif (
                doc_id
                and sem_key
                and isinstance(doc_id, str)
                and isinstance(sem_key, str)
                and doc_id.strip()
                and sem_key.strip()
            ):
                dedup_key = ("document_semantic", doc_id.strip(), sem_key.strip())
            else:
                dedup_key = None

            if dedup_key is None:
                unkeyed_documents.append(doc)
                continue

            score = extract_and_validate_score(doc)

            if dedup_key not in best_by_key:
                best_by_key[dedup_key] = doc
            else:
                existing_doc = best_by_key[dedup_key]
                existing_score = extract_and_validate_score(existing_doc)
                if score > existing_score:
                    best_by_key[dedup_key] = doc
                elif score == existing_score:
                    # Deterministic tie-breaker: compare canonical document fingerprints
                    if canonical_document_fingerprint(doc) < canonical_document_fingerprint(existing_doc):
                        best_by_key[dedup_key] = doc

        return list(best_by_key.values()) + unkeyed_documents

    def order_documents(self, documents: List[Any]) -> List[Any]:
        """Orders documents using deterministic 6-level sort rule:
        1. score descending (higher similarity first)
        2. parent-before-child ordering (parent chunks before child chunks using parent_chunk_id flag)
        3. document_id ascending
        4. line_start ascending
        5. chunk_id ascending
        6. canonical_document_fingerprint ascending (final deterministic tie-breaker)
        """
        def sort_key(doc: Any) -> Tuple[float, int, str, int, str, str]:
            meta = getattr(doc, "metadata", {}) or {}
            score = extract_and_validate_score(doc)
            is_child = 1 if meta.get("parent_chunk_id") else 0
            doc_id = str(meta.get("document_id", "") or "")
            loc = meta.get("source_location")
            line_start = 0
            if isinstance(loc, dict):
                line_start = loc.get("line_start") or 0
            chunk_id = str(meta.get("chunk_id", "") or "")
            fp = canonical_document_fingerprint(doc)
            return (-score, is_child, doc_id, line_start, chunk_id, fp)

        return sorted(documents, key=sort_key)

    def build_context(self, documents: List[Any]) -> str:
        """Synthesizes structured, token-bounded prompt context.
        
        Consumes ONLY sanitized content from Document.page_content.
        """
        if not documents:
            return ""

        # Step 1: Deduplicate documents preserving highest score with fingerprint tie-breaking
        deduped = self.deduplicate_documents(documents)

        # Step 2: Sort deterministically across all 6 levels
        ordered = self.order_documents(deduped)

        # Step 3: Token-budgeted synthesis
        accumulated_sections: List[str] = []
        current_tokens = 0

        for doc in ordered:
            content = getattr(doc, "page_content", "") or ""
            meta = getattr(doc, "metadata", {}) or {}

            section_parts: List[str] = []
            if self.include_citations:
                section_parts.append(self._format_citation(meta))
            section_parts.append(content)
            section_str = "\n".join(section_parts)

            section_tokens = self._safe_estimate_tokens(section_str)

            # Check token budget
            if current_tokens + section_tokens <= self.max_tokens:
                accumulated_sections.append(section_str)
                current_tokens += section_tokens
            else:
                # Stop when budget exceeded
                break

        return "\n\n".join(accumulated_sections)
