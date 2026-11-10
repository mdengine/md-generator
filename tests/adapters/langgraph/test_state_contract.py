"""Tests for MDEngineGraphState schema typing and runtime validation."""

import pytest
from md_generator.adapters.langgraph.exceptions import GraphStateValidationError
from md_generator.adapters.langgraph.state import (
    ALLOWED_ROUTES,
    DocumentStateDTO,
    MDEngineGraphState,
    validate_graph_state,
)
from md_generator.vector.exceptions import TenantBoundaryError


def test_state_requires_non_empty_tenant():
    """State lacking tenant_id or with empty/whitespace tenant must raise TenantBoundaryError."""
    with pytest.raises(TenantBoundaryError, match="missing mandatory 'tenant_id'"):
        validate_graph_state({})

    with pytest.raises(TenantBoundaryError, match="must be a non-empty string"):
        validate_graph_state({"tenant_id": ""})

    with pytest.raises(TenantBoundaryError, match="must be a non-empty string"):
        validate_graph_state({"tenant_id": "   "})

    with pytest.raises(TenantBoundaryError, match="must be a non-empty string"):
        validate_graph_state({"tenant_id": 123})


def test_state_non_dict_rejected():
    """Non-dict state inputs must be rejected with TenantBoundaryError."""
    with pytest.raises(TenantBoundaryError, match="must be a dictionary"):
        validate_graph_state(["tenant-1"])  # type: ignore[arg-type]


def test_state_valid_minimal_and_full():
    """State with only tenant_id or all valid fields must pass validation."""
    # Minimal
    tenant = validate_graph_state({"tenant_id": "tenant-corp"})
    assert tenant == "tenant-corp"

    # Full
    state: MDEngineGraphState = {
        "tenant_id": "tenant-corp",
        "query": "search term",
        "documents": [{"page_content": "hello", "metadata": {"tenant_id": "tenant-corp"}}],
        "context": "Context text",
        "route": "synthesize",
        "metadata": {"execution_time_ms": 12.5},
        "error": None,
    }
    assert validate_graph_state(state) == "tenant-corp"


def test_state_field_type_validations():
    """Declared fields must adhere strictly to schema types."""
    # query must be str or None
    with pytest.raises(GraphStateValidationError, match="'query' must be a string"):
        validate_graph_state({"tenant_id": "T1", "query": 123})

    # documents must be list or None
    with pytest.raises(GraphStateValidationError, match="'documents' must be a list"):
        validate_graph_state({"tenant_id": "T1", "documents": "not-a-list"})

    # context must be str or None
    with pytest.raises(GraphStateValidationError, match="'context' must be a string"):
        validate_graph_state({"tenant_id": "T1", "context": 456})

    # route must be str in ALLOWED_ROUTES or None
    with pytest.raises(GraphStateValidationError, match="'route' must be a string"):
        validate_graph_state({"tenant_id": "T1", "route": 123})

    with pytest.raises(GraphStateValidationError, match="'route' must be one of"):
        validate_graph_state({"tenant_id": "T1", "route": "unknown_route"})

    # metadata must be dict or None
    with pytest.raises(GraphStateValidationError, match="'metadata' must be a dictionary"):
        validate_graph_state({"tenant_id": "T1", "metadata": [1, 2]})

    # error must be str or None
    with pytest.raises(GraphStateValidationError, match="'error' must be a string"):
        validate_graph_state({"tenant_id": "T1", "error": 500})


def test_state_unknown_keys_preserved():
    """Unknown keys are preserved for downstream agents if serializable."""
    state = {
        "tenant_id": "tenant-corp",
        "agent_scratchpad": "thought: search documents",
        "step_counter": 3,
    }
    assert validate_graph_state(state) == "tenant-corp"
