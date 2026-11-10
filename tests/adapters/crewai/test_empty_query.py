"""Tests for empty query schema validation rejection and zero search results contracts (P2B-V06)."""

from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError
from langchain_core.documents import Document

from md_generator.adapters.crewai import MDSearchTool


@pytest.mark.parametrize("empty_query", ["", "   ", "\t\n  ", None])
def test_tool_run_rejects_empty_query_via_validation_error(empty_query):
    """Empty or whitespace-only query passed to run() must raise pydantic.ValidationError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod")

    with pytest.raises(ValidationError):
        tool.run(query=empty_query)

    mock_retriever.invoke.assert_not_called()


def test_tool_run_zero_retrieval_results():
    """Valid query yielding zero documents from retriever returns deterministic informative string."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = []
    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod")

    res = tool.run(query="quantum cryptography")
    assert res == "No relevant documents found for query: 'quantum cryptography'."
    mock_retriever.invoke.assert_called_once_with("quantum cryptography")


def test_tool_run_all_documents_below_score_threshold():
    """Valid query where all documents are filtered by min_score returns zero results string."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="Weak match", metadata={"tenant_id": "tenant-prod", "score": 0.40}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.75)
    res = tool.run(query="unmatched topic")
    assert res == "No relevant documents found for query: 'unmatched topic'."
