"""Tests for order-independent routing and deterministic permutations (P2A-R06)."""

import itertools
import pytest
from langchain_core.documents import Document
from md_generator.adapters.langgraph.nodes import create_router_node


def test_router_order_independent_all_permutations():
    """All 6 permutations of document scores [0.30, 0.91, 0.40] with threshold 0.80
    must route to 'context' based on max(scores) == 0.91."""
    scores = [0.30, 0.91, 0.40]
    threshold = 0.80

    for perm in itertools.permutations(scores):
        router = create_router_node(min_score=threshold, trusted_tenant="tenant-A")
        docs = [
            Document(page_content=f"Doc {s}", metadata={"tenant_id": "tenant-A", "score": s})
            for s in perm
        ]
        state = {"tenant_id": "tenant-A", "documents": docs}
        assert router(state) == "context"


def test_router_below_threshold_all_permutations():
    """All permutations where max(scores) < threshold must route to 'fallback'."""
    scores = [0.30, 0.75, 0.40]
    threshold = 0.80

    for perm in itertools.permutations(scores):
        router = create_router_node(min_score=threshold, trusted_tenant="tenant-A")
        docs = [
            Document(page_content=f"Doc {s}", metadata={"tenant_id": "tenant-A", "score": s})
            for s in perm
        ]
        state = {"tenant_id": "tenant-A", "documents": docs}
        assert router(state) == "fallback"


def test_router_exact_threshold_boundary():
    """Document score exactly equal to threshold must route to 'context'."""
    router = create_router_node(min_score=0.80, trusted_tenant="tenant-A")
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="Exact", metadata={"tenant_id": "tenant-A", "score": 0.80}),
        ],
    }
    assert router(state) == "context"


def test_router_empty_documents_routes_to_fallback():
    """Empty documents list must immediately route to 'fallback'."""
    router = create_router_node(min_score=0.0, trusted_tenant="tenant-A")
    state = {"tenant_id": "tenant-A", "documents": []}
    assert router(state) == "fallback"


def test_router_none_documents_routes_to_fallback():
    """None documents field must immediately route to 'fallback'."""
    router = create_router_node(min_score=0.0, trusted_tenant="tenant-A")
    state = {"tenant_id": "tenant-A", "documents": None}
    assert router(state) == "fallback"


def test_router_single_document_above_and_below():
    """Single document routing correctly tests boundary."""
    router = create_router_node(min_score=0.60, trusted_tenant="tenant-A")
    doc_high = Document(page_content="High", metadata={"tenant_id": "tenant-A", "score": 0.65})
    doc_low = Document(page_content="Low", metadata={"tenant_id": "tenant-A", "score": 0.55})

    assert router({"tenant_id": "tenant-A", "documents": [doc_high]}) == "context"
    assert router({"tenant_id": "tenant-A", "documents": [doc_low]}) == "fallback"
