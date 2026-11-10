"""Tests for Phase 1C import isolation and optional dependency behavior."""

import sys
import subprocess
import pytest


def test_core_isolation_zero_ai_leakage():
    """Validates that importing core mdengine modules does not leak any langchain packages into sys.modules."""
    code = """
import sys
import md_generator.pipeline
import md_generator.semantic
import md_generator.vector

leaked = [
    m for m in sys.modules
    if any(m.startswith(prefix) for prefix in [
        "langchain", "langchain_core", "langchain_community", "langgraph", "crewai"
    ])
]
assert len(leaked) == 0, f"Leaked AI framework packages into core sys.modules: {leaked}"
print("CORE_ISOLATION_CLEAN")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Core isolation failed:\n{result.stderr}"
    assert "CORE_ISOLATION_CLEAN" in result.stdout


def test_missing_langchain_dependency_isolation():
    """Validates behavior when langchain-core is completely unavailable.
    
    1. Importing md_generator.adapters.langchain succeeds without error.
    2. Calling loader.lazy_load() raises LangChainDependencyError.
    3. Calling loader.load() raises LangChainDependencyError.
    4. Instantiating MDVectorStoreRetriever raises LangChainDependencyError.
    """
    code = """
import sys

# Block langchain and langchain_core imports
sys.modules['langchain'] = None
sys.modules['langchain_core'] = None
sys.modules['langchain_core.document_loaders'] = None
sys.modules['langchain_core.documents'] = None
sys.modules['langchain_core.retrievers'] = None
sys.modules['langchain_core.callbacks'] = None

from md_generator.adapters.langchain import (
    MDDocumentLoader,
    MDVectorStoreRetriever,
    PromptContextBuilder,
    LangChainDependencyError,
)
from md_generator.semantic.model.schema import SemanticChunk

chunk = SemanticChunk(
    chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
    document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
    sanitized_content="hello",
)
loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-alpha")

# 1. lazy_load() must raise LangChainDependencyError
try:
    list(loader.lazy_load())
    assert False, "lazy_load() should have raised LangChainDependencyError"
except LangChainDependencyError:
    pass

# 2. load() must raise LangChainDependencyError
try:
    loader.load()
    assert False, "load() should have raised LangChainDependencyError"
except LangChainDependencyError:
    pass

# 3. MDVectorStoreRetriever init must raise LangChainDependencyError
try:
    MDVectorStoreRetriever(store=None, provider=None, tenant_id="t1")
    assert False, "MDVectorStoreRetriever should have raised LangChainDependencyError"
except LangChainDependencyError:
    pass

# 4. PromptContextBuilder operates stdlib-only and succeeds
builder = PromptContextBuilder()
assert builder.build_context([]) == ""

print("MISSING_DEPENDENCY_ISOLATION_CLEAN")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Missing dependency isolation failed:\n{result.stderr}"
    assert "MISSING_DEPENDENCY_ISOLATION_CLEAN" in result.stdout


def test_active_langchain_integration():
    """Validates that when langchain-core is active, classes properly subclass LangChain ABCs."""
    from langchain_core.document_loaders import BaseLoader
    from langchain_core.retrievers import BaseRetriever
    from md_generator.adapters.langchain import MDDocumentLoader, MDVectorStoreRetriever

    assert issubclass(MDDocumentLoader, BaseLoader)
    assert issubclass(MDVectorStoreRetriever, BaseRetriever)
