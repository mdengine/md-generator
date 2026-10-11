"""Tests for explicit document score validation and router threshold bounds (P2A-R02, P2A-R05)."""

import math
import pytest
from langchain_core.documents import Document
from md_generator.adapters.langgraph.exceptions import GraphRoutingError
from md_generator.adapters.langgraph.nodes import create_router_node


@pytest.mark.parametrize(
    "valid_score",
    [0.92, 0.0, 1.0, 0, 1, 0.5],
)
def test_router_accepts_valid_numeric_scores(valid_score):
    """Valid numeric scores within [0.0, 1.0] must be processed successfully."""
    router = create_router_node(min_score=0.5, trusted_tenant="tenant-A")
    doc = Document(page_content="Text", metadata={"tenant_id": "tenant-A", "score": valid_score})
    state = {"tenant_id": "tenant-A", "documents": [doc]}
    expected_route = "context" if float(valid_score) >= 0.5 else "fallback"
    assert router(state) == expected_route


@pytest.mark.parametrize(
    "invalid_score,error_match",
    [
        (None, "has None 'score'"),
        (True, "has boolean 'score'"),
        (False, "has boolean 'score'"),
        ("0.92", "non-numeric score"),
        (float("nan"), "non-finite score"),
        (float("inf"), "non-finite score"),
        (float("-inf"), "non-finite score"),
        (-0.1, r"outside \[0\.0, 1\.0\]"),
        (1.1, r"outside \[0\.0, 1\.0\]"),
    ],
)
def test_router_rejects_invalid_score_values(invalid_score, error_match):
    """Invalid score types, booleans, strings, non-finites, and out-of-bound scores must raise GraphRoutingError."""
    router = create_router_node(min_score=0.5, trusted_tenant="tenant-A")
    doc = Document(page_content="Text", metadata={"tenant_id": "tenant-A", "score": invalid_score})
    state = {"tenant_id": "tenant-A", "documents": [doc]}
    with pytest.raises(GraphRoutingError, match=error_match):
        router(state)


def test_router_rejects_missing_score_field():
    """Document lacking 'score' key entirely must raise GraphRoutingError."""
    router = create_router_node(min_score=0.5, trusted_tenant="tenant-A")
    doc = Document(page_content="Text", metadata={"tenant_id": "tenant-A"})
    state = {"tenant_id": "tenant-A", "documents": [doc]}
    with pytest.raises(GraphRoutingError, match="missing mandatory 'score' field"):
        router(state)


@pytest.mark.parametrize(
    "valid_threshold",
    [0.0, 0.5, 1.0, 0, 1],
)
def test_router_construction_valid_thresholds(valid_threshold):
    """Valid numeric thresholds within [0.0, 1.0] succeed at construction."""
    router = create_router_node(min_score=valid_threshold, trusted_tenant="tenant-A")
    assert callable(router)


@pytest.mark.parametrize(
    "invalid_threshold,error_match",
    [
        ("0.5", "must be a numeric float or int"),
        (True, "cannot be a boolean"),
        (False, "cannot be a boolean"),
        (None, "must be a numeric float or int"),
        (float("nan"), "cannot be NaN or Infinite"),
        (float("inf"), "cannot be NaN or Infinite"),
        (float("-inf"), "cannot be NaN or Infinite"),
        (-0.1, "must be between 0.0 and 1.0"),
        (1.1, "must be between 0.0 and 1.0"),
    ],
)
def test_router_construction_invalid_thresholds(invalid_threshold, error_match):
    """Invalid threshold types, booleans, strings, non-finites, and out-of-bound thresholds raise ValueError."""
    with pytest.raises(ValueError, match=error_match):
        create_router_node(min_score=invalid_threshold, trusted_tenant="tenant-A")
