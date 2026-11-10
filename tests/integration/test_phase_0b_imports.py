"""Integration Import Isolation Test for Phase 0B.

Verifies that importing Phase 0B packages (metadata, lineage, security) executes
cleanly without leaking or requiring third-party AI framework packages in sys.modules.
"""

import sys
import pytest


def test_phase_0b_imports_isolation():
    import md_generator.metadata
    import md_generator.lineage
    import md_generator.security

    # Assert that no third-party AI packages were implicitly imported into sys.modules
    prohibited_packages = [
        "langchain",
        "langchain_core",
        "langgraph",
        "crewai",
        "qdrant_client",
        "chromadb",
        "neo4j",
        "openai",
        "ollama",
    ]

    for pkg in prohibited_packages:
        assert pkg not in sys.modules, f"Forbidden third-party AI package '{pkg}' was implicitly imported into sys.modules!"
