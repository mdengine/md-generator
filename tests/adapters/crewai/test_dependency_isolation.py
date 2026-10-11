"""Tests for Phase 2B dependency isolation, zero core leakage, and exception uncoupling (Gate 7, Gate 8, Gate 9, P2B-R03)."""

from importlib.machinery import ModuleSpec
import subprocess
import sys
from unittest.mock import MagicMock, patch
import pytest

from md_generator.adapters.crewai import (
    CrewAIAdapterError,
    CrewAIDependencyError,
    CrewAIToolExecutionError,
    TenantBoundaryError,
    detect_crewai_base_tool,
)
from md_generator.adapters.langgraph.exceptions import LangGraphAdapterError
from md_generator.vector.exceptions import EmbeddingProviderError, VectorStoreError


def test_core_isolation_zero_crewai_leakage():
    """Validates that importing core mdengine modules does not leak crewai into sys.modules (Gate 8)."""
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


def test_dependency_detection_environment_1_genuinely_absent():
    """Environment 1: When crewai and crewai_tools are genuinely absent, returns None (activates fallback)."""
    with patch("importlib.util.find_spec", return_value=None):
        base_tool = detect_crewai_base_tool()
        assert base_tool is None


def test_dependency_detection_environment_2_supported_crewai():
    """Environment 2: When supported CrewAI is installed, returns detected BaseTool."""
    dummy_spec = ModuleSpec("crewai", None)
    dummy_base_tool = type("MockCrewAIBaseTool", (), {})

    def mock_find_spec(name, *args, **kwargs):
        if name == "crewai":
            return dummy_spec
        return None

    with patch("importlib.util.find_spec", side_effect=mock_find_spec):
        with patch.dict("sys.modules", {"crewai.tools": MagicMock(BaseTool=dummy_base_tool)}):
            base_tool = detect_crewai_base_tool()
            assert base_tool is dummy_base_tool


def test_dependency_detection_environment_3_broken_installation():
    """Environment 3: When package is found but BaseTool import fails, raises CrewAIDependencyError (P2B-R03)."""
    dummy_spec = ModuleSpec("crewai", None)

    def mock_find_spec(name, *args, **kwargs):
        if name == "crewai":
            return dummy_spec
        return None

    # Simulate broken internal import inside installed crewai
    with patch("importlib.util.find_spec", side_effect=mock_find_spec):
        with patch("builtins.__import__", side_effect=ImportError("No module named 'crewai.internal_broken'")):
            with pytest.raises(CrewAIDependencyError, match="crewai is installed but BaseTool cannot be imported"):
                detect_crewai_base_tool()


def test_dependency_detection_corrupted_metadata_raises():
    """When package metadata finder raises error, raises CrewAIDependencyError (P2B-R03)."""
    with patch("importlib.util.find_spec", side_effect=ValueError("Corrupted spec")):
        with pytest.raises(CrewAIDependencyError, match="Corrupted crewai package metadata"):
            detect_crewai_base_tool()


def test_missing_crewai_dependency_graceful_subprocess():
    """Validates subprocess fallback execution when crewai is not installed."""
    code = """
import sys
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
    while TenantBoundaryError is preserved directly for security violations (P2B-R02)."""
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
