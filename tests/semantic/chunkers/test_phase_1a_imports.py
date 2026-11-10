"""Import isolation test for Phase 1A modules to verify zero third-party AI package leakage."""

import sys


def test_phase_1a_imports_zero_ai_framework_leakage():
    # Import Phase 1A modules
    import md_generator.semantic.chunkers.base
    import md_generator.semantic.chunkers.identity
    import md_generator.semantic.chunkers.code
    import md_generator.semantic.chunkers.openapi
    import md_generator.semantic.chunkers.sap
    import md_generator.semantic.chunkers.db
    import md_generator.semantic.chunkers.registry
    import md_generator.semantic.processor

    forbidden = [
        "langchain",
        "langgraph",
        "crewai",
        "qdrant_client",
        "chromadb",
        "neo4j",
        "llama_index",
    ]

    leaked = [mod for mod in forbidden if any(loaded.startswith(mod) for loaded in sys.modules)]
    assert leaked == [], f"Third-party AI frameworks leaked into sys.modules: {leaked}"
