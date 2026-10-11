"""Tests for empty query handling and error preservation across fallback (P2A-R07)."""

import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document
from md_generator.adapters.langgraph.nodes import create_fallback_node, create_retrieval_node
from md_generator.adapters.langgraph.state import MDEngineGraphState


def test_retrieval_node_empty_string_query():
    """Empty string query must return empty documents list and explicit error."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-test"
    node = create_retrieval_node(mock_retriever, trusted_tenant="tenant-test")

    state: MDEngineGraphState = {"tenant_id": "tenant-test", "query": ""}
    res = node(state)

    assert res["documents"] == []
    assert res["error"] == "Query string is empty or absent."
    mock_retriever.invoke.assert_not_called()


def test_retrieval_node_whitespace_query():
    """Whitespace query must return empty documents list and explicit error."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-test"
    node = create_retrieval_node(mock_retriever, trusted_tenant="tenant-test")

    state: MDEngineGraphState = {"tenant_id": "tenant-test", "query": "   \t\n  "}
    res = node(state)

    assert res["documents"] == []
    assert res["error"] == "Query string is empty or absent."
    mock_retriever.invoke.assert_not_called()


def test_retrieval_node_none_query():
    """None query must return empty documents list and explicit error."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-test"
    node = create_retrieval_node(mock_retriever, trusted_tenant="tenant-test")

    state: MDEngineGraphState = {"tenant_id": "tenant-test", "query": None}
    res = node(state)

    assert res["documents"] == []
    assert res["error"] == "Query string is empty or absent."
    mock_retriever.invoke.assert_not_called()


def test_fallback_node_preserves_retrieval_error():
    """Fallback node must NOT overwrite or clear existing retrieval error."""
    fallback_node = create_fallback_node(trusted_tenant="tenant-test")

    # Simulate state transition: retrieve produced error, then fallback runs
    state: MDEngineGraphState = {
        "tenant_id": "tenant-test",
        "query": "",
        "documents": [],
        "error": "Query string is empty or absent.",
    }

    update = fallback_node(state)
    assert update["route"] == "fallback"
    assert update["context"] == ""
    # update does not include 'error', so LangGraph state merge leaves state['error'] intact
    assert "error" not in update

    merged_state = {**state, **update}
    assert merged_state["error"] == "Query string is empty or absent."
    assert merged_state["route"] == "fallback"
    assert merged_state["context"] == ""
    assert merged_state["documents"] == []


def test_valid_query_zero_results_has_no_error():
    """Valid query yielding zero results produces no error, routes to fallback."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-test"
    mock_retriever.invoke.return_value = []
    retrieval_node = create_retrieval_node(mock_retriever, trusted_tenant="tenant-test")
    fallback_node = create_fallback_node(trusted_tenant="tenant-test")

    initial_state: MDEngineGraphState = {
        "tenant_id": "tenant-test",
        "query": "unmatched search term",
    }
    retrieval_update = retrieval_node(initial_state)
    assert retrieval_update["documents"] == []
    assert "error" not in retrieval_update

    state_after_retrieval = {**initial_state, **retrieval_update}
    assert state_after_retrieval.get("error") is None

    fallback_update = fallback_node(state_after_retrieval)
    final_state = {**state_after_retrieval, **fallback_update}

    assert final_state["documents"] == []
    assert final_state["context"] == ""
    assert final_state["route"] == "fallback"
    assert final_state.get("error") is None
