"""Security tests for MDSearchTool tenant boundary and document ownership enforcement."""

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from md_generator.adapters.crewai import MDSearchTool, TenantBoundaryError


@pytest.mark.parametrize("invalid_tenant", [None, "", "   ", 123, True, []])
def test_tool_construction_rejects_invalid_tenant_id(invalid_tenant):
    """Construction must strictly reject non-string, empty, whitespace-only, or None tenant IDs."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"

    with pytest.raises(TenantBoundaryError, match="requires a mandatory non-empty string 'tenant_id'"):
        MDSearchTool(retriever=mock_retriever, tenant_id=invalid_tenant)


def test_tool_construction_rejects_retriever_tenant_mismatch():
    """Tool tenant_id mismatching retriever.tenant_id must raise TenantBoundaryError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"

    with pytest.raises(TenantBoundaryError, match="conflicts with retriever tenant_id 'tenant-A'"):
        MDSearchTool(retriever=mock_retriever, tenant_id="tenant-B")


def test_tool_execution_rejects_foreign_document():
    """Retrieved document belonging to foreign tenant must raise TenantBoundaryError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"
    mock_retriever.invoke.return_value = [
        Document(page_content="Foreign Text", metadata={"tenant_id": "tenant-B", "score": 0.95}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-A")
    with pytest.raises(TenantBoundaryError, match="belongs to tenant 'tenant-B', conflicting with bound tool tenant 'tenant-A'"):
        tool.run(query="search")


def test_tool_execution_rejects_missing_document_tenant():
    """Retrieved document missing tenant_id metadata must raise TenantBoundaryError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"
    mock_retriever.invoke.return_value = [
        Document(page_content="Text", metadata={"score": 0.95}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-A")
    with pytest.raises(TenantBoundaryError, match="missing mandatory non-empty 'tenant_id'"):
        tool.run(query="search")


def test_tool_execution_rejects_empty_document_tenant():
    """Retrieved document with empty string tenant_id must raise TenantBoundaryError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"
    mock_retriever.invoke.return_value = [
        Document(page_content="Text", metadata={"tenant_id": "", "score": 0.95}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-A")
    with pytest.raises(TenantBoundaryError, match="missing mandatory non-empty 'tenant_id'"):
        tool.run(query="search")


def test_tool_execution_rejects_whitespace_document_tenant():
    """Retrieved document with whitespace-only tenant_id must raise TenantBoundaryError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"
    mock_retriever.invoke.return_value = [
        Document(page_content="Text", metadata={"tenant_id": "   \t  ", "score": 0.95}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-A")
    with pytest.raises(TenantBoundaryError, match="missing mandatory non-empty 'tenant_id'"):
        tool.run(query="search")


def test_tool_execution_rejects_mixed_tenant_documents():
    """Collection with 1 valid and 1 foreign document must raise TenantBoundaryError before returning."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"
    mock_retriever.invoke.return_value = [
        Document(page_content="Valid Text", metadata={"tenant_id": "tenant-A", "score": 0.95}),
        Document(page_content="Foreign Text", metadata={"tenant_id": "tenant-B", "score": 0.85}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-A")
    with pytest.raises(TenantBoundaryError, match="belongs to tenant 'tenant-B'"):
        tool.run(query="search")


def test_tenant_boundary_error_not_wrapped_in_execution_error():
    """Validates TenantBoundaryError is raised directly and is uncoupled from CrewAIAdapterError (P2B-R02)."""
    from md_generator.adapters.crewai import CrewAIAdapterError

    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-A"
    mock_retriever.invoke.return_value = [
        Document(page_content="Foreign Text", metadata={"tenant_id": "tenant-B", "score": 0.95}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-A")
    try:
        tool.run(query="search")
    except Exception as exc:
        assert isinstance(exc, TenantBoundaryError)
        assert not isinstance(exc, CrewAIAdapterError)
