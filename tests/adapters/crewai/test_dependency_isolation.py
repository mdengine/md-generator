"""Tests for Phase 2B dependency isolation, zero core leakage, and exception uncoupling (Gate 8, Gate 9)."""

import subprocess
import sys

from md_generator.adapters.crewai.exceptions import (
    CrewAIAdapterError,
    CrewAIDependencyError,
    CrewAIToolExecutionError,
    TenantBoundaryError,
)
from md_generator.adapters.langgraph.exceptions import LangGraphAdapterError
from md_generator.vector.exceptions import EmbeddingProviderError, VectorStoreError


def test_core_isolation_zero_crewai_leakage():
    """Validates that importing core mdengine modules does not leak crewai into sys.modules."""
    code = """
import sys
import md_generator.pipeline
import md_generator.semantic
import md_generator.vector

leaked = [
    m for m in sys.modules
    if any(m.startswith(prefix) for prefix in [
        "crewai", "crewai_tools"
    ])
]
assert len(leaked) == 0, f"Leaked crewai packages into core sys.modules: {leaked}"
print("CORE_ISOLATION_CLEAN")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Core isolation failed:\n{result.stderr}"
    assert "CORE_ISOLATION_CLEAN" in result.stdout


def test_missing_crewai_dependency_graceful_import():
    """Validates that importing md_generator.adapters.crewai succeeds cleanly when crewai is absent."""
    code = """
import sys

# Block crewai and crewai_tools
sys.modules['crewai'] = None
sys.modules['crewai.tools'] = None
sys.modules['crewai_tools'] = None

from md_generator.adapters.crewai import MDSearchTool, MDSearchInput, CrewAIAdapterError
from unittest.mock import MagicMock

mock_retriever = MagicMock()
mock_retriever.tenant_id = "tenant-standalone"
mock_retriever.invoke.return_value = []

tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-standalone")
assert tool.name == "enterprise_knowledge_search"
res = tool.run(query="test query")
assert "No relevant documents found" in res
print("FALLBACK_EXECUTION_CLEAN")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Missing dependency execution failed:\n{result.stderr}"
    assert "FALLBACK_EXECUTION_CLEAN" in result.stdout


def test_exception_uncoupling_and_shared_tenant_boundary():
    """Validates that CrewAI adapter exceptions are uncoupled from vector and graph hierarchies,
    while TenantBoundaryError is preserved directly for security violations."""
    # Hierarchy within CrewAI domain
    assert issubclass(CrewAIDependencyError, CrewAIAdapterError)
    assert issubclass(CrewAIToolExecutionError, CrewAIAdapterError)

    # Completely uncoupled from vector store errors
    assert not issubclass(CrewAIAdapterError, VectorStoreError)
    assert not issubclass(CrewAIAdapterError, EmbeddingProviderError)
    assert not issubclass(VectorStoreError, CrewAIAdapterError)

    # Completely uncoupled from LangGraph adapter errors
    assert not issubclass(CrewAIAdapterError, LangGraphAdapterError)
    assert not issubclass(LangGraphAdapterError, CrewAIAdapterError)

    # Shared TenantBoundaryError is distinct from CrewAIAdapterError
    assert not issubclass(TenantBoundaryError, CrewAIAdapterError)
    assert not issubclass(CrewAIAdapterError, TenantBoundaryError)
