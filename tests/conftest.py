"""Root conftest ensuring import isolation across test suites."""

import sys
import pytest


@pytest.fixture(autouse=True)
def clean_ai_imports_for_isolation_tests(request):
    """Ensures sys.modules is isolated when running Phase 1A import isolation test."""
    if "test_phase_1a_imports" in request.node.nodeid:
        forbidden = [
            "langchain",
            "langchain_core",
            "langchain_community",
            "langgraph",
            "crewai",
            "qdrant_client",
            "chromadb",
            "neo4j",
            "llama_index",
            "md_generator.adapters",
        ]
        for m in list(sys.modules.keys()):
            if any(m == p or m.startswith(p + ".") or m.startswith(p + "_") for p in forbidden):
                sys.modules.pop(m, None)
