"""Security tests for deep document-level tenant ownership and state tenant boundaries (P2A-R01)."""

import pytest
from langchain_core.documents import Document
from md_generator.adapters.langgraph.state import DocumentStateDTO, validate_graph_state
from md_generator.vector.exceptions import TenantBoundaryError


def test_tenant_boundary_matching_state_and_documents_pass():
    """tenant-A state + tenant-A documents must pass validation."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content 1", metadata={"tenant_id": "tenant-A", "score": 0.9}),
            {"page_content": "Content 2", "metadata": {"tenant_id": "tenant-A", "score": 0.85}},
        ],
    }
    assert validate_graph_state(state, trusted_tenant="tenant-A") == "tenant-A"


def test_tenant_boundary_foreign_document_rejected():
    """tenant-A state + tenant-B document must immediately raise TenantBoundaryError."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content 1", metadata={"tenant_id": "tenant-B", "score": 0.9}),
        ],
    }
    with pytest.raises(TenantBoundaryError, match="belongs to tenant 'tenant-B', conflicting with graph trusted tenant 'tenant-A'"):
        validate_graph_state(state, trusted_tenant="tenant-A")


def test_tenant_boundary_document_missing_tenant_rejected():
    """tenant-A state + document missing tenant_id must raise TenantBoundaryError."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content 1", metadata={"score": 0.9}),
        ],
    }
    with pytest.raises(TenantBoundaryError, match="missing mandatory non-empty 'tenant_id' in metadata"):
        validate_graph_state(state, trusted_tenant="tenant-A")


def test_tenant_boundary_document_empty_tenant_rejected():
    """tenant-A state + document with empty tenant_id must raise TenantBoundaryError."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            {"page_content": "Content 1", "metadata": {"tenant_id": "", "score": 0.9}},
        ],
    }
    with pytest.raises(TenantBoundaryError, match="missing mandatory non-empty 'tenant_id' in metadata"):
        validate_graph_state(state, trusted_tenant="tenant-A")


def test_tenant_boundary_document_whitespace_tenant_rejected():
    """tenant-A state + document with whitespace-only tenant_id must raise TenantBoundaryError."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content 1", metadata={"tenant_id": "   ", "score": 0.9}),
        ],
    }
    with pytest.raises(TenantBoundaryError, match="missing mandatory non-empty 'tenant_id' in metadata"):
        validate_graph_state(state, trusted_tenant="tenant-A")


def test_tenant_boundary_mixed_tenant_documents_rejected():
    """Collection with 1 valid tenant-A doc and 1 foreign tenant-B doc must raise TenantBoundaryError."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content A", metadata={"tenant_id": "tenant-A", "score": 0.9}),
            Document(page_content="Content B", metadata={"tenant_id": "tenant-B", "score": 0.85}),
        ],
    }
    with pytest.raises(TenantBoundaryError, match="conflicting with graph trusted tenant 'tenant-A'"):
        validate_graph_state(state, trusted_tenant="tenant-A")


def test_tenant_boundary_mixed_document_and_dto_collection():
    """Mixed collection containing Document and DocumentStateDTO objects must validate both."""
    # Valid mixed collection
    valid_state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content Doc", metadata={"tenant_id": "tenant-A", "score": 0.9}),
            {"page_content": "Content DTO", "metadata": {"tenant_id": "tenant-A", "score": 0.8}},
        ],
    }
    assert validate_graph_state(valid_state, trusted_tenant="tenant-A") == "tenant-A"

    # Invalid mixed collection (DTO has bad tenant)
    invalid_state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Content Doc", metadata={"tenant_id": "tenant-A", "score": 0.9}),
            {"page_content": "Content DTO", "metadata": {"tenant_id": "tenant-C", "score": 0.8}},
        ],
    }
    with pytest.raises(TenantBoundaryError, match="belongs to tenant 'tenant-C'"):
        validate_graph_state(invalid_state, trusted_tenant="tenant-A")


def test_tenant_boundary_top_level_state_conflict():
    """Top-level state tenant mismatching trusted_tenant must raise TenantBoundaryError."""
    with pytest.raises(TenantBoundaryError, match="State tenant_id 'tenant-B' conflicts with bound graph trusted tenant 'tenant-A'"):
        validate_graph_state({"tenant_id": "tenant-B"}, trusted_tenant="tenant-A")
