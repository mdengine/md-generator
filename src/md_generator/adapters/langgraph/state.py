"""LangGraph state contracts with explicit requiredness, document-level tenant checks, and recursive serialization."""

import math
from typing import Any, Dict, List, Optional, Sequence, Union
from typing_extensions import NotRequired, Required, TypedDict

from md_generator.adapters.langgraph.exceptions import GraphStateValidationError
from md_generator.vector.exceptions import TenantBoundaryError

__all__ = [
    "DocumentStateDTO",
    "MDEngineGraphState",
    "ALLOWED_ROUTES",
    "validate_serializable_value",
    "validate_graph_state",
]


class DocumentStateDTO(TypedDict):
    """Serializable document transfer object for LangGraph checkpoint state."""
    page_content: str
    metadata: Dict[str, Any]


class MDEngineGraphState(TypedDict, total=False):
    """State contract for mdengine LangGraph workflows.
    
    Fields:
        tenant_id: Required[str] - Mandatory, non-empty, strictly immutable across all transitions.
        query: NotRequired[Optional[str]] - Input search query.
        documents: NotRequired[List[Any]] - Retrieved documents (replacement semantics, no operator.add).
        context: NotRequired[Optional[str]] - Synthesized token-budgeted prompt context.
        route: NotRequired[Optional[str]] - Persisted routing decision ('synthesize' | 'fallback').
        metadata: NotRequired[Dict[str, Any]] - Execution telemetry, audit trail, and timestamps.
        error: NotRequired[Optional[str]] - Failure trace description.
    """
    tenant_id: Required[str]
    query: NotRequired[Optional[str]]
    documents: NotRequired[List[Any]]
    context: NotRequired[Optional[str]]
    route: NotRequired[Optional[str]]
    metadata: NotRequired[Dict[str, Any]]
    error: NotRequired[Optional[str]]


ALLOWED_ROUTES = {"synthesize", "fallback"}


def validate_serializable_value(val: Any, path: str = "state") -> None:
    """Recursively validates that a value satisfies strict JSON/msgpack serialization.
    
    Permits: None, str, bool, int, finite float, list/tuple of serializables, dict with str keys.
    Rejects: Non-finite floats (NaN, Inf), unpicklable objects, sockets, functions, client handles.
    """
    if val is None or isinstance(val, (str, bool, int)):
        return
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            raise GraphStateValidationError(
                f"Non-finite float not permitted in serializable state at '{path}': {val}"
            )
        return
    if isinstance(val, (list, tuple)):
        for i, item in enumerate(val):
            validate_serializable_value(item, f"{path}[{i}]")
        return
    if isinstance(val, dict):
        for k, item in val.items():
            if not isinstance(k, str):
                raise GraphStateValidationError(
                    f"Dictionary keys must be strings at '{path}': got {type(k).__name__}"
                )
            validate_serializable_value(item, f"{path}.{k}")
        return
    # LangChain Document instance or duck-typed Document
    if hasattr(val, "page_content") and hasattr(val, "metadata"):
        if not isinstance(val.page_content, str):
            raise GraphStateValidationError(f"Document.page_content must be str at '{path}'")
        if not isinstance(val.metadata, dict):
            raise GraphStateValidationError(f"Document.metadata must be dict at '{path}'")
        validate_serializable_value(val.metadata, f"{path}.metadata")
        return
    raise GraphStateValidationError(
        f"Unsupported non-serializable object of type '{type(val).__name__}' at '{path}'"
    )


def validate_graph_state(
    state: Dict[str, Any],
    trusted_tenant: Optional[str] = None,
) -> str:
    """Comprehensive runtime validation of graph state compliance.
    
    Invariants:
        1. Verifies state is a dictionary with non-empty string tenant_id.
        2. Enforces top-level tenant_id matches trusted_tenant if provided.
        3. DEEP DOCUMENT VALIDATION (P2A-R01): Verifies EVERY document in state['documents']
           has metadata['tenant_id'] matching trusted_tenant.
        4. RECURSIVE SERIALIZATION (P2A-R04): Validates document metadata, state metadata,
           and any unknown keys to guarantee strict JSON/msgpack serializability.
        5. Validates types for query, documents, context, route, error.
        
    Raises:
        TenantBoundaryError: If tenant_id is missing/empty, mismatches trusted_tenant,
                             or ANY document has a missing/conflicting tenant_id.
        GraphStateValidationError: If any field violates typing or serialization constraints.
    """
    if not isinstance(state, dict):
        raise TenantBoundaryError("Graph state must be a dictionary or TypedDict instance.")
    
    # 1. Top-level tenant validation
    tenant_id = state.get("tenant_id")
    if tenant_id is None:
        raise TenantBoundaryError("Graph state missing mandatory 'tenant_id'.")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise TenantBoundaryError("Graph state 'tenant_id' must be a non-empty string.")
    
    tenant_id = tenant_id.strip()
    if trusted_tenant is not None:
        trusted_tenant = trusted_tenant.strip()
        if tenant_id != trusted_tenant:
            raise TenantBoundaryError(
                f"State tenant_id '{tenant_id}' conflicts with bound graph trusted tenant '{trusted_tenant}'."
            )
    effective_tenant = trusted_tenant or tenant_id

    # 2. Query validation
    query = state.get("query")
    if query is not None and not isinstance(query, str):
        raise GraphStateValidationError(f"'query' must be a string or None, got {type(query).__name__}.")
        
    # 3. Documents validation with deep document-level tenant enforcement (P2A-R01)
    docs = state.get("documents")
    if docs is not None:
        if not isinstance(docs, list):
            raise GraphStateValidationError(f"'documents' must be a list or None, got {type(docs).__name__}.")
        for i, doc in enumerate(docs):
            if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                meta = doc.metadata
            elif isinstance(doc, dict) and "page_content" in doc:
                meta = doc.get("metadata", {})
            else:
                raise GraphStateValidationError(
                    f"Document at index {i} must be a Document instance or dict with 'page_content'."
                )
            if not isinstance(meta, dict):
                raise GraphStateValidationError(f"Document at index {i} metadata must be a dictionary.")

            # Document-level tenant ownership enforcement
            doc_tenant = meta.get("tenant_id")
            if doc_tenant is None or not isinstance(doc_tenant, str) or not doc_tenant.strip():
                raise TenantBoundaryError(
                    f"Document at index {i} missing mandatory non-empty 'tenant_id' in metadata."
                )
            if doc_tenant.strip() != effective_tenant:
                raise TenantBoundaryError(
                    f"Document at index {i} belongs to tenant '{doc_tenant.strip()}', "
                    f"conflicting with graph trusted tenant '{effective_tenant}'."
                )
            # Recursive serialization check on document metadata
            validate_serializable_value(meta, f"documents[{i}].metadata")

    # 4. Context validation
    context = state.get("context")
    if context is not None and not isinstance(context, str):
        raise GraphStateValidationError(f"'context' must be a string or None, got {type(context).__name__}.")

    # 5. Route validation
    route = state.get("route")
    if route is not None:
        if not isinstance(route, str):
            raise GraphStateValidationError(f"'route' must be a string or None, got {type(route).__name__}.")
        if route not in ALLOWED_ROUTES:
            raise GraphStateValidationError(f"'route' must be one of {ALLOWED_ROUTES}, got '{route}'.")

    # 6. Metadata validation
    meta = state.get("metadata")
    if meta is not None:
        if not isinstance(meta, dict):
            raise GraphStateValidationError(f"'metadata' must be a dictionary or None, got {type(meta).__name__}.")
        validate_serializable_value(meta, "metadata")

    # 7. Error validation
    err = state.get("error")
    if err is not None and not isinstance(err, str):
        raise GraphStateValidationError(f"'error' must be a string or None, got {type(err).__name__}.")

    # 8. Validate any unknown preserved keys for serialization safety
    known_keys = {"tenant_id", "query", "documents", "context", "route", "metadata", "error"}
    for k, v in state.items():
        if k not in known_keys:
            validate_serializable_value(v, k)

    return tenant_id
