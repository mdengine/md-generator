"""End-to-end tool execution tests for MDSearchTool (run() and _run()) and exception wrapping (P2B-R01, P2B-R02)."""

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document
from pydantic import ValidationError

from md_generator.adapters.crewai import MDSearchTool
from md_generator.adapters.crewai.exceptions import CrewAIToolExecutionError
from md_generator.adapters.langchain.context import PromptContextBuilder


def test_tool_execution_run_and_internal_run_equivalent():
    """Validates that public run() and internal _run() methods return identical results."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-e2e"
    mock_retriever.invoke.return_value = [
        Document(
            page_content="Enterprise architectural invariant details.",
            metadata={"tenant_id": "tenant-e2e", "score": 0.92, "document_id": "doc-arch"},
        ),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-e2e")

    res_public = tool.run(query="architecture")
    res_internal = tool._run(query="architecture")
    res_positional = tool.run("architecture")

    assert res_public == res_internal == res_positional
    assert "Enterprise architectural invariant details." in res_public
    assert "Source: doc-arch" in res_public


def test_tool_execution_state_remains_unmutated_across_calls():
    """Tool instance state, tenant_id, and min_score remain strictly unchanged across multiple invocations."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-e2e"
    mock_retriever.invoke.return_value = [
        Document(page_content="Result 1", metadata={"tenant_id": "tenant-e2e", "score": 0.88}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-e2e", min_score=0.5)

    assert tool.tenant_id == "tenant-e2e"
    assert tool.min_score == 0.5

    # Invocations
    tool.run(query="query 1")
    tool.run(query="query 2")

    assert tool.tenant_id == "tenant-e2e"
    assert tool.min_score == 0.5
    assert mock_retriever.invoke.call_count == 2


def test_tool_execution_dict_kwargs_parsing():
    """Tool execution correctly parses dictionary kwargs payload."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-e2e"
    mock_retriever.invoke.return_value = [
        Document(page_content="Payload text", metadata={"tenant_id": "tenant-e2e", "score": 0.95}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-e2e")
    payload = {"query": "sample search"}
    res = tool.run(**payload)

    assert "Payload text" in res


def test_tool_execution_rejects_extra_fields_via_kwargs():
    """Passing extra fields (e.g. agent tenant override) via kwargs raises ValidationError (P2B-R02)."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-e2e"

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-e2e")
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        tool.run(query="search", tenant_id="intruder-tenant")

    mock_retriever.invoke.assert_not_called()


def test_tool_execution_retriever_failure_wrapped_in_execution_error():
    """Retriever runtime failure is wrapped in CrewAIToolExecutionError (P2B-R02)."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-e2e"
    mock_retriever.invoke.side_effect = RuntimeError("Database connection pool exhausted")

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-e2e")
    with pytest.raises(CrewAIToolExecutionError, match="Retriever invocation failed"):
        tool.run(query="failing search")


def test_tool_execution_context_builder_failure_wrapped_in_execution_error():
    """Context synthesis failure is wrapped in CrewAIToolExecutionError (P2B-R02)."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-e2e"
    mock_retriever.invoke.return_value = [
        Document(page_content="Doc Content", metadata={"tenant_id": "tenant-e2e", "score": 0.95}),
    ]
    mock_builder = MagicMock()
    mock_builder.build_context.side_effect = RuntimeError("Synthesis buffer overflow")

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-e2e", builder=mock_builder)
    with pytest.raises(CrewAIToolExecutionError, match="Context synthesis failed"):
        tool.run(query="synthesis failure search")
