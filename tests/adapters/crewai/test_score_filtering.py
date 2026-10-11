"""Tests for MDSearchTool construction-time threshold bounds and document score filtering."""

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from md_generator.adapters.crewai import MDSearchTool
from md_generator.adapters.crewai.exceptions import CrewAIToolExecutionError


@pytest.mark.parametrize("valid_score", [0.0, 0.5, 1.0, 0, 1])
def test_tool_construction_valid_min_score(valid_score):
    """Valid numeric thresholds within [0.0, 1.0] are accepted."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=valid_score)
    assert tool.min_score == float(valid_score)


@pytest.mark.parametrize(
    "invalid_score,error_match",
    [
        (True, "min_score cannot be a boolean"),
        (False, "min_score cannot be a boolean"),
        ("0.5", "must be a numeric float or int"),
        (None, "must be a numeric float or int"),
        (float("nan"), "cannot be NaN or Infinite"),
        (float("inf"), "cannot be NaN or Infinite"),
        (float("-inf"), "cannot be NaN or Infinite"),
        (-0.1, r"must be between 0\.0 and 1\.0"),
        (1.1, r"must be between 0\.0 and 1\.0"),
    ],
)
def test_tool_construction_invalid_min_score_rejected(invalid_score, error_match):
    """Invalid threshold types, booleans, strings, non-finites, and out-of-bound values raise ValueError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    with pytest.raises(ValueError, match=error_match):
        MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=invalid_score)


@pytest.mark.parametrize(
    "bad_doc_score,error_match",
    [
        (None, "has None 'score'"),
        (True, "has boolean 'score'"),
        (False, "has boolean 'score'"),
        ("0.9", "has non-numeric score"),
        (float("nan"), "has non-finite score"),
        (float("inf"), "has non-finite score"),
        (float("-inf"), "has non-finite score"),
        (-0.1, r"outside \[0\.0, 1\.0\]"),
        (1.1, r"outside \[0\.0, 1\.0\]"),
    ],
)
def test_tool_execution_rejects_invalid_document_scores(bad_doc_score, error_match):
    """Retrieved document with invalid score type, boolean, non-finite, or out-of-bounds raises CrewAIToolExecutionError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="Bad Score Doc", metadata={"tenant_id": "tenant-prod", "score": bad_doc_score}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.5)
    with pytest.raises(CrewAIToolExecutionError, match=error_match):
        tool.run(query="search")


def test_tool_execution_rejects_missing_document_score():
    """Retrieved document missing 'score' key entirely raises CrewAIToolExecutionError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="No Score Doc", metadata={"tenant_id": "tenant-prod"}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.5)
    with pytest.raises(CrewAIToolExecutionError, match="missing mandatory 'score'"):
        tool.run(query="search")


def test_tool_filters_documents_below_threshold():
    """Documents strictly below min_score are filtered out before context synthesis."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="High Relevance Doc", metadata={"tenant_id": "tenant-prod", "score": 0.90, "document_id": "doc1"}),
        Document(page_content="Low Relevance Doc", metadata={"tenant_id": "tenant-prod", "score": 0.60, "document_id": "doc2"}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.80)
    result = tool.run(query="search")

    assert "High Relevance Doc" in result
    assert "Low Relevance Doc" not in result
