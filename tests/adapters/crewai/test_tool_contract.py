"""Tests for MDSearchTool metadata contract and tenant immutability."""

from unittest.mock import MagicMock
import pytest

from md_generator.adapters.crewai import MDSearchInput, MDSearchTool
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
