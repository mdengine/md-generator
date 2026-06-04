from md_generator.sap.graph.backends.memory import InMemoryGraphStore
from md_generator.sap.graph.backends.protocol import GraphStore


def test_in_memory_graph_store_satisfies_protocol():
    store: GraphStore = InMemoryGraphStore(graph_id="test")
    assert store.graph.graph_id == "test"
