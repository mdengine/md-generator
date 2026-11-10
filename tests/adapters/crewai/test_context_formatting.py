"""Tests for MDSearchTool integration with PromptContextBuilder and citation formatting."""

from unittest.mock import MagicMock
from langchain_core.documents import Document

from md_generator.adapters.crewai import MDSearchTool
from md_generator.adapters.langchain.context import PromptContextBuilder


def test_tool_formats_context_with_citations_and_score_ordering():
    """Tool returns deterministic context ordered by score with citation headers."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-corp"
    mock_retriever.invoke.return_value = [
        Document(
            page_content="Content B with lower score",
            metadata={"tenant_id": "tenant-corp", "score": 0.85, "document_id": "doc-B", "chunk_id": "c-B"},
        ),
        Document(
            page_content="Content A with higher score",
            metadata={"tenant_id": "tenant-corp", "score": 0.98, "document_id": "doc-A", "chunk_id": "c-A"},
        ),
    ]

    builder = PromptContextBuilder(max_tokens=2000, include_citations=True)
    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-corp", builder=builder)

    context = tool.run(query="enterprise guidelines")

    assert "Source: doc-A" in context
    assert "Source: doc-B" in context
    assert "Content A with higher score" in context
    assert "Content B with lower score" in context
    # Higher score appears first
    pos_a = context.find("Content A")
    pos_b = context.find("Content B")
    assert pos_a < pos_b


def test_tool_adheres_to_builder_token_budget():
    """Tool adheres to PromptContextBuilder maximum estimated token limit."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-corp"
    mock_retriever.invoke.return_value = [
        Document(
            page_content="Chunk 1 short content",
            metadata={"tenant_id": "tenant-corp", "score": 0.95, "document_id": "doc-1"},
        ),
        Document(
            page_content="Chunk 2 " + ("word " * 50),
            metadata={"tenant_id": "tenant-corp", "score": 0.90, "document_id": "doc-2"},
        ),
    ]

    # Constrained token budget
    builder = PromptContextBuilder(max_tokens=30, include_citations=False)
    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-corp", builder=builder)

    context = tool.run(query="short summary")
    # Only the first chunk should fit within the tight budget
    assert "Chunk 1" in context
    assert "Chunk 2" not in context


def test_tool_positional_and_keyword_invocations_identical():
    """Calling tool.run('query') and tool.run(query='query') produce identical results."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-corp"
    mock_retriever.invoke.return_value = [
        Document(
            page_content="Sample Content",
            metadata={"tenant_id": "tenant-corp", "score": 0.90, "document_id": "doc-1"},
        ),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-corp")

    res_pos = tool.run("lookup query")
    res_kw = tool.run(query="lookup query")

    assert res_pos == res_kw
    assert "Sample Content" in res_pos
