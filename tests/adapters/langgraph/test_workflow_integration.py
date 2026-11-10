"""End-to-end integration tests for compiled StateGraph RAG workflow (build_rag_workflow)."""

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.adapters.langgraph.graph import build_rag_workflow
from md_generator.vector.exceptions import TenantBoundaryError


def test_workflow_high_relevance_synthesizes_context():
    """Documents above threshold route through 'context' and synthesize prompt context."""
    retriever = MagicMock()
    retriever.tenant_id = "tenant-prod"
    retriever.invoke.return_value = [
        Document(
            page_content="High relevance chunk content",
            metadata={"tenant_id": "tenant-prod", "score": 0.88, "document_id": "doc-1", "chunk_id": "c-1"},
        ),
    ]

    builder = PromptContextBuilder(max_tokens=2000, include_citations=True)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.70)

    final_state = app.invoke({"tenant_id": "tenant-prod", "query": "important question"})

    assert final_state["tenant_id"] == "tenant-prod"
    assert final_state["route"] == "synthesize"
    assert "High relevance chunk content" in final_state["context"]
    assert "Source: doc-1" in final_state["context"]
    assert final_state.get("error") is None
    assert len(final_state["documents"]) == 1


def test_workflow_low_relevance_routes_to_fallback():
    """Documents below threshold route through 'fallback' and produce empty context."""
    retriever = MagicMock()
    retriever.tenant_id = "tenant-prod"
    retriever.invoke.return_value = [
        Document(
            page_content="Low relevance chunk content",
            metadata={"tenant_id": "tenant-prod", "score": 0.45, "document_id": "doc-2"},
        ),
    ]

    builder = PromptContextBuilder(max_tokens=2000)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.70)

    final_state = app.invoke({"tenant_id": "tenant-prod", "query": "marginal question"})

    assert final_state["tenant_id"] == "tenant-prod"
    assert final_state["route"] == "fallback"
    assert final_state["context"] == ""
    assert final_state.get("error") is None


def test_workflow_zero_results_routes_to_fallback():
    """Retriever yielding zero results routes through 'fallback' with no error."""
    retriever = MagicMock()
    retriever.tenant_id = "tenant-prod"
    retriever.invoke.return_value = []

    builder = PromptContextBuilder(max_tokens=2000)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.70)

    final_state = app.invoke({"tenant_id": "tenant-prod", "query": "unknown topic"})

    assert final_state["tenant_id"] == "tenant-prod"
    assert final_state["route"] == "fallback"
    assert final_state["context"] == ""
    assert final_state["documents"] == []
    assert final_state.get("error") is None


def test_workflow_empty_query_routes_to_fallback_with_error():
    """Empty query routes through 'fallback' and strictly preserves the error."""
    retriever = MagicMock()
    retriever.tenant_id = "tenant-prod"

    builder = PromptContextBuilder(max_tokens=2000)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.70)

    final_state = app.invoke({"tenant_id": "tenant-prod", "query": "   "})

    assert final_state["tenant_id"] == "tenant-prod"
    assert final_state["route"] == "fallback"
    assert final_state["context"] == ""
    assert final_state["documents"] == []
    assert final_state["error"] == "Query string is empty or absent."
    retriever.invoke.assert_not_called()


def test_workflow_tenant_mismatch_raises_boundary_error():
    """Input tenant mismatching bound retriever tenant must immediately raise TenantBoundaryError."""
    retriever = MagicMock()
    retriever.tenant_id = "tenant-prod"

    builder = PromptContextBuilder(max_tokens=2000)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.50)

    with pytest.raises(TenantBoundaryError, match="conflicts with bound graph trusted tenant 'tenant-prod'"):
        app.invoke({"tenant_id": "tenant-intruder", "query": "exploit"})


def test_workflow_state_metadata_telemetry_preserved():
    """State metadata dictionary (audit trail, correlation_id) is preserved through workflow transitions."""
    retriever = MagicMock()
    retriever.tenant_id = "tenant-prod"
    retriever.invoke.return_value = [
        Document(page_content="Content", metadata={"tenant_id": "tenant-prod", "score": 0.9}),
    ]

    builder = PromptContextBuilder(max_tokens=1000)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.50)

    initial_input = {
        "tenant_id": "tenant-prod",
        "query": "hello",
        "metadata": {
            "correlation_id": "corr-uuid-9999",
            "telemetry_data": {"caller": "api_gateway", "retries": 0},
        },
    }
    final_state = app.invoke(initial_input)

    assert final_state["metadata"]["correlation_id"] == "corr-uuid-9999"
    assert final_state["metadata"]["telemetry_data"] == {"caller": "api_gateway", "retries": 0}
