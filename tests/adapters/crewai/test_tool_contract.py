"""Tests for MDSearchTool metadata contract, tenant immutability, and invocation signatures (P2B-R01)."""

from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError

from md_generator.adapters.crewai import MDSearchInput, MDSearchTool
from md_generator.adapters.crewai.tools import _FallbackBaseTool
from md_generator.adapters.langchain.context import PromptContextBuilder


def test_tool_metadata_contract():
    """Validates public attributes and schema metadata on MDSearchTool."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod")

    assert tool.name == "enterprise_knowledge_search"
    assert "Search enterprise markdown and code documentation" in tool.description
    assert tool.args_schema is MDSearchInput
    assert tool.tenant_id == "tenant-prod"
    assert tool.min_score == 0.0
    assert tool.retriever is mock_retriever
    assert isinstance(tool.builder, PromptContextBuilder)


def test_fallback_base_tool_public_surface():
    """Validates that _FallbackBaseTool provides the complete public compatibility surface."""
    fallback = _FallbackBaseTool()
    assert fallback.name == "enterprise_knowledge_search"
    assert "Search enterprise markdown and code documentation" in fallback.description
    assert fallback.args_schema is MDSearchInput
    assert callable(fallback.run)
    assert callable(fallback._run)


def test_tool_tenant_id_immutability():
    """Validates that tenant_id cannot be mutated after construction."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod")

    with pytest.raises(AttributeError, match="tenant_id is immutable"):
        tool.tenant_id = "tenant-intruder"

    with pytest.raises(AttributeError, match="tenant_id is immutable"):
        tool._tenant_id = "tenant-intruder"

    assert tool.tenant_id == "tenant-prod"


def test_invocation_signatures_keyword_and_positional():
    """Validates both keyword and positional invocation forms on run() and _run() (P2B-R01)."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = []

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod")

    # 1. Keyword run()
    res1 = tool.run(query="test keyword run")
    assert "No relevant documents found for query: 'test keyword run'" in res1

    # 2. Keyword _run()
    res2 = tool._run(query="test keyword _run")
    assert "No relevant documents found for query: 'test keyword _run'" in res2

    # 3. Positional run()
    res3 = tool.run("test positional run")
    assert "No relevant documents found for query: 'test positional run'" in res3

    # 4. Positional _run()
    res4 = tool._run("test positional _run")
    assert "No relevant documents found for query: 'test positional _run'" in res4


def test_invocation_signatures_rejections():
    """Validates that invalid invocation patterns raise pydantic.ValidationError (P2B-R01, P2B-R02)."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod")

    # Missing arguments
    with pytest.raises(ValidationError):
        tool.run()

    with pytest.raises(ValidationError):
        tool._run()

    # Unexpected extra keyword argument
    with pytest.raises(ValidationError):
        tool.run(query="hello", unexpected_field="bad")

    # Runtime tenant_id injection attempt
    with pytest.raises(ValidationError):
        tool.run(query="hello", tenant_id="tenant-injected")

    # Multiple positional arguments
    with pytest.raises(ValidationError):
        tool.run("query1", "query2")

    # Both positional and keyword query provided
    with pytest.raises(ValidationError):
        tool.run("positional_query", query="keyword_query")

    # Non-string positional argument
    with pytest.raises(ValidationError):
        tool.run(12345)

    with pytest.raises(ValidationError):
        tool.run(None)
