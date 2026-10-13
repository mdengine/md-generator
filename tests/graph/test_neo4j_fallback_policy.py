from unittest.mock import patch
import pytest

from md_generator.graph.exceptions import Neo4jDependencyError
from md_generator.graph.stores.neo4j import Neo4jGraphStore, GraphStoreFactory
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_neo4j_fallback_policy_no_silent_downgrade():
    # Simulate neo4j module missing
    with patch("md_generator.graph.stores.neo4j._is_neo4j_available", return_value=False):
        # Default fallback_to_memory=False MUST raise Neo4jDependencyError
        with pytest.raises(Neo4jDependencyError):
            Neo4jGraphStore(uri="bolt://localhost:7687", fallback_to_memory=False)

        # Explicit fallback_to_memory=True succeeds and uses fallback store
        store = Neo4jGraphStore(uri="bolt://localhost:7687", fallback_to_memory=True)
        assert store._fallback_store is not None
        assert isinstance(store._fallback_store, InMemoryGraphStore)


def test_graph_store_factory_creation():
    store_mem = GraphStoreFactory.create(provider="in_memory")
    assert isinstance(store_mem, InMemoryGraphStore)

    # Factory with fallback_to_memory
    with patch("md_generator.graph.stores.neo4j._is_neo4j_available", return_value=False):
        with pytest.raises(Neo4jDependencyError):
            GraphStoreFactory.create(provider="neo4j", fallback_to_memory=False)

        store_fallback = GraphStoreFactory.create(provider="neo4j", fallback_to_memory=True)
        assert isinstance(store_fallback, Neo4jGraphStore)
        assert store_fallback._fallback_store is not None

    # Invalid provider
    with pytest.raises(ValueError):
        GraphStoreFactory.create(provider="unknown_provider")  # type: ignore
