"""Functional node factories with document-level tenant validation and order-independent routing."""

import math
from typing import Any, Callable, Dict, List, Optional
from md_generator.adapters.langchain.context import PromptContextBuilder, extract_and_validate_score
from md_generator.adapters.langchain.retriever import MDVectorStoreRetriever
from md_generator.adapters.langgraph.exceptions import GraphRoutingError, GraphStateValidationError
from md_generator.adapters.langgraph.state import MDEngineGraphState, validate_graph_state
from md_generator.vector.exceptions import TenantBoundaryError

__all__ = [
    "to_langchain_document",
    "create_retrieval_node",
    "create_context_builder_node",
    "create_fallback_node",
    "create_router_node",
]

try:
    from langchain_core.documents import Document
except ImportError:
    class Document:  # type: ignore[no-redef]
        def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
            self.page_content = page_content
            self.metadata = metadata or {}


def to_langchain_document(doc: Any) -> Any:
    """Converts a DocumentStateDTO dictionary or Document instance into a standard Document object (P2A-R03)."""
    if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
        return doc
    if isinstance(doc, dict) and "page_content" in doc:
        return Document(page_content=str(doc["page_content"]), metadata=dict(doc.get("metadata", {})))
    raise GraphStateValidationError(f"Cannot convert object of type '{type(doc).__name__}' to Document.")


def create_retrieval_node(
    retriever: MDVectorStoreRetriever,
    trusted_tenant: str,
) -> Callable[[MDEngineGraphState], Dict[str, Any]]:
    """Creates a retrieval node bound to an MDVectorStoreRetriever.
    
    Terminal Empty Query Contract (P2A-R07):
        If query is empty or whitespace, returns {'documents': [], 'error': 'Query string is empty or absent.'}.
    """
    def retrieval_node(state: MDEngineGraphState) -> Dict[str, Any]:
        validate_graph_state(state, trusted_tenant=trusted_tenant)
        query = state.get("query")
        if not query or not isinstance(query, str) or not query.strip():
            return {"documents": [], "error": "Query string is empty or absent."}
        
        docs = retriever.invoke(query.strip())
        return {"documents": docs}

    return retrieval_node


def create_context_builder_node(
    builder: PromptContextBuilder,
    trusted_tenant: str,
) -> Callable[[MDEngineGraphState], Dict[str, Any]]:
    """Creates a context synthesis node bound to a PromptContextBuilder.
    
    Converts any DocumentStateDTO dictionaries to Document objects before invoking builder.build_context().
    """
    def context_builder_node(state: MDEngineGraphState) -> Dict[str, Any]:
        validate_graph_state(state, trusted_tenant=trusted_tenant)
        raw_docs = state.get("documents", []) or []
        standardized_docs = [to_langchain_document(d) for d in raw_docs]
        context = builder.build_context(standardized_docs)
        return {"context": context, "route": "synthesize"}

    return context_builder_node


def create_fallback_node(
    trusted_tenant: str,
) -> Callable[[MDEngineGraphState], Dict[str, Any]]:
    """Creates a fallback node executed when retrieval produces no results or fails threshold.
    
    Preserves any existing error in state while setting route to 'fallback'.
    """
    def fallback_node(state: MDEngineGraphState) -> Dict[str, Any]:
        validate_graph_state(state, trusted_tenant=trusted_tenant)
        return {"context": "", "route": "fallback"}

    return fallback_node


def create_router_node(
    min_score: float,
    trusted_tenant: str,
    has_docs_route: str = "context",
    fallback_route: str = "fallback",
) -> Callable[[MDEngineGraphState], str]:
    """Creates an order-independent conditional routing function evaluating document relevance.
    
    Invariants:
        1. Validates min_score strictly: float/int, not bool, not NaN, not Inf, in [0.0, 1.0] (P2A-R05).
        2. Validates state tenant and deep document tenant ownership (P2A-R01).
        3. If state['documents'] is empty, ALWAYS returns fallback_route.
        4. ORDER-INDEPENDENT SCORE EVALUATION (P2A-R06): Calculates max_score across all documents.
        5. EXPLICIT SCORE REJECTION (P2A-R02): Documents missing 'score', None, bool, str, NaN, Inf
           raise GraphRoutingError immediately without fallback substitution.
        6. If max_score >= min_score, returns has_docs_route; otherwise fallback_route.
    """
    if isinstance(min_score, bool):
        raise ValueError("min_score cannot be a boolean.")
    if not isinstance(min_score, (int, float)):
        raise ValueError(f"min_score must be a numeric float or int, got {type(min_score).__name__}.")
    min_score_val = float(min_score)
    if math.isnan(min_score_val) or math.isinf(min_score_val):
        raise ValueError("min_score cannot be NaN or Infinite.")
    if not (0.0 <= min_score_val <= 1.0):
        raise ValueError(f"min_score must be between 0.0 and 1.0, got {min_score_val}.")

    def router_node(state: MDEngineGraphState) -> str:
        docs = state.get("documents", []) or []
        for i, doc in enumerate(docs):
            meta = doc.metadata if hasattr(doc, "metadata") else (doc.get("metadata", {}) if isinstance(doc, dict) else {})
            if "score" not in meta:
                raise GraphRoutingError(f"Document at index {i} is missing mandatory 'score' field in metadata.")
            raw_score = meta["score"]
            if raw_score is None:
                raise GraphRoutingError(f"Document at index {i} has None 'score'.")
            if isinstance(raw_score, bool):
                raise GraphRoutingError(f"Document at index {i} has boolean 'score', which is strictly rejected.")
            if not isinstance(raw_score, (int, float)):
                raise GraphRoutingError(
                    f"Document at index {i} has non-numeric score of type '{type(raw_score).__name__}'."
                )
            if math.isnan(raw_score) or math.isinf(raw_score):
                raise GraphRoutingError(f"Document at index {i} has non-finite score: {raw_score}")
            if not (0.0 <= raw_score <= 1.0):
                raise GraphRoutingError(f"Document at index {i} score {raw_score} is outside [0.0, 1.0].")

        validate_graph_state(state, trusted_tenant=trusted_tenant)
        if not docs:
            return fallback_route
        
        max_score = -1.0
        for i, doc in enumerate(docs):
            meta = doc.metadata if hasattr(doc, "metadata") else doc.get("metadata", {})
            if "score" not in meta:
                raise GraphRoutingError(f"Document at index {i} is missing mandatory 'score' field in metadata.")
            raw_score = meta["score"]
            if raw_score is None:
                raise GraphRoutingError(f"Document at index {i} has None 'score'.")
            if isinstance(raw_score, bool):
                raise GraphRoutingError(f"Document at index {i} has boolean 'score', which is strictly rejected.")
            if not isinstance(raw_score, (int, float)):
                raise GraphRoutingError(
                    f"Document at index {i} has non-numeric score of type '{type(raw_score).__name__}'."
                )
            if math.isnan(raw_score) or math.isinf(raw_score):
                raise GraphRoutingError(f"Document at index {i} has non-finite score: {raw_score}")
            if not (0.0 <= raw_score <= 1.0):
                raise GraphRoutingError(f"Document at index {i} score {raw_score} is outside [0.0, 1.0].")
            
            # Use Phase 1C score validation contract
            try:
                score_val = extract_and_validate_score(to_langchain_document(doc))
            except (ValueError, TypeError) as e:
                raise GraphRoutingError(f"Document at index {i} contains invalid relevance score: {e}") from e
                
            if score_val > max_score:
                max_score = score_val

        if max_score >= min_score_val:
            return has_docs_route
        return fallback_route

    return router_node
