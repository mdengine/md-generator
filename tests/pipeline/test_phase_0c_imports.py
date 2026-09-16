from __future__ import annotations

import sys
import pytest


def test_phase_0c_imports_zero_ai_framework_leakage():
    # Import Phase 0C public pipeline API
    import md_generator.pipeline

    # Prohibited third-party AI packages
    prohibited_prefixes = [
        "langchain",
        "langgraph",
        "crewai",
        "qdrant_client",
        "chromadb",
        "neo4j",
        "openai",
        "ollama",
        "llama_index",
    ]

    leaked = [
        mod
        for mod in sys.modules
        if any(mod == p or mod.startswith(p + ".") for p in prohibited_prefixes)
    ]

    assert leaked == [], f"Third-party AI package leaks detected in sys.modules: {leaked}"
