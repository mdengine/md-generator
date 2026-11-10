"""Tests for Phase 2A dependency isolation, core import boundaries, and exception uncoupling (Gate 11, Gate 12)."""

import subprocess
import sys
import pytest

from md_generator.adapters.langgraph.exceptions import (
    GraphRoutingError,
    GraphStateValidationError,
    LangGraphAdapterError,
    LangGraphDependencyError,
)
from md_generator.vector.exceptions import EmbeddingProviderError, VectorStoreError


def test_core_isolation_zero_langgraph_leakage():
    """Validates that importing core mdengine modules does not leak langgraph into sys.modules."""
    code = """
import sys
import md_generator.pipeline
import md_generator.semantic
import md_generator.vector

leaked = [
    m for m in sys.modules
    if any(m.startswith(prefix) for prefix in [
        "langgraph", "langgraph_checkpoint", "crewai"
    ])
]
assert len(leaked) == 0, f"Leaked packages into core sys.modules: {leaked}"
print("CORE_ISOLATION_CLEAN")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Core isolation failed:\n{result.stderr}"
    assert "CORE_ISOLATION_CLEAN" in result.stdout


def test_missing_langgraph_dependency_isolation():
    """Validates behavior when langgraph is not installed or unavailable."""
    code = """
import sys
from unittest.mock import MagicMock

# Block langgraph
sys.modules['langgraph'] = None
sys.modules['langgraph.graph'] = None
sys.modules['langgraph.checkpoint'] = None

from md_generator.adapters.langgraph import (
    build_rag_workflow,
    LangGraphDependencyError,
    validate_graph_state,
)

# 1. State validation works without langgraph
state = {'tenant_id': 'tenant-test'}
assert validate_graph_state(state, trusted_tenant='tenant-test') == 'tenant-test'

# 2. build_rag_workflow raises LangGraphDependencyError
mock_retriever = MagicMock()
mock_retriever.tenant_id = 'tenant-test'
mock_builder = MagicMock()

try:
    build_rag_workflow(retriever=mock_retriever, builder=mock_builder)
    assert False, "build_rag_workflow should have raised LangGraphDependencyError"
except LangGraphDependencyError:
    pass

print("MISSING_DEPENDENCY_CLEAN")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Missing dependency isolation failed:\n{result.stderr}"
    assert "MISSING_DEPENDENCY_CLEAN" in result.stdout


def test_exception_uncoupling():
    """Validates that LangGraph adapter errors are completely uncoupled from vector-domain errors."""
    # Graph errors inherit from LangGraphAdapterError
    assert issubclass(LangGraphDependencyError, LangGraphAdapterError)
    assert issubclass(GraphStateValidationError, LangGraphAdapterError)
    assert issubclass(GraphRoutingError, LangGraphAdapterError)

    # Graph errors DO NOT inherit from vector store or embedding provider errors
    assert not issubclass(LangGraphAdapterError, VectorStoreError)
    assert not issubclass(LangGraphAdapterError, EmbeddingProviderError)
    assert not issubclass(GraphStateValidationError, VectorStoreError)
    assert not issubclass(GraphRoutingError, VectorStoreError)

    # Vector store errors DO NOT inherit from LangGraphAdapterError
    assert not issubclass(VectorStoreError, LangGraphAdapterError)
    assert not issubclass(EmbeddingProviderError, LangGraphAdapterError)
