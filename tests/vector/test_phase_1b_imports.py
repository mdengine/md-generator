"""Unit tests for Phase 1B import isolation and zero third-party AI framework leakage."""

import sys
import pytest


def test_phase_1b_zero_ai_framework_leakage():
    # Remove mock third-party modules if placed by other tests
    forbidden_prefixes = [
        "langchain",
        "langgraph",
        "crewai",
        "qdrant_client",
        "chromadb",
        "sentence_transformers",
        "openai",
        "neo4j",
    ]
    to_del = [
        m for m in sys.modules
        if any(m == p or m.startswith(p + ".") for p in forbidden_prefixes)
    ]
    for m in to_del:
        del sys.modules[m]

    # Import core Phase 1B vector models and stdlib store
    from md_generator.vector import (
        EmbeddingRecord,
        VectorQueryResult,
        CollectionConfig,
        VectorSyncRecord,
        VectorSyncManifest,
        VectorSyncManifestStore,
        EmbeddingProcessor,
    )
    from md_generator.vector.providers import MockEmbeddingProvider
    from md_generator.vector.stores import InMemoryVectorStore

    # Verify no third-party AI frameworks have leaked into sys.modules
    leaked = [
        m for m in sys.modules
        if any(m == p or m.startswith(p + ".") for p in forbidden_prefixes)
    ]
    assert leaked == [], f"Third-party AI packages leaked into sys.modules during vector import: {leaked}"
