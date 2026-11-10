import pytest

from md_generator.graph.exceptions import GraphQueryError
from md_generator.graph.model import EntityNode, RelationEdge
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_neighbor_resource_limits():
    store = InMemoryGraphStore()
    center = EntityNode(node_id="center", tenant_id="t1", entity_id="c", entity_type="hub", name="C", qualified_name="C")
    store.upsert_nodes([center], tenant_id="t1")

    # Add 10 leaf nodes
    leaves = [
        EntityNode(node_id=f"leaf-{i}", tenant_id="t1", entity_id=f"l{i}", entity_type="leaf", name=f"L{i}", qualified_name=f"L{i}")
        for i in range(10)
    ]
    edges = [
        RelationEdge(edge_id=f"e-{i}", tenant_id="t1", source_id="center", target_id=f"leaf-{i}", relationship_type="CONNECTS")
        for i in range(10)
    ]
    store.upsert_nodes(leaves, tenant_id="t1")
    store.upsert_edges(edges, tenant_id="t1")

    # Relaxed mode: truncates to max_nodes=5
    nbrs = store.get_neighbors("center", tenant_id="t1", max_nodes=5, strict_limits=False)
    assert len(nbrs) == 5

    # Strict mode: raises GraphQueryError
    with pytest.raises(GraphQueryError):
        store.get_neighbors("center", tenant_id="t1", max_nodes=5, strict_limits=True)


def test_traversal_resource_limits_and_metadata():
    store = InMemoryGraphStore()
    center = EntityNode(node_id="center", tenant_id="t1", entity_id="c", entity_type="hub", name="C", qualified_name="C")
    store.upsert_nodes([center], tenant_id="t1")

    leaves = [
        EntityNode(node_id=f"leaf-{i}", tenant_id="t1", entity_id=f"l{i}", entity_type="leaf", name=f"L{i}", qualified_name=f"L{i}")
        for i in range(20)
    ]
    edges = [
        RelationEdge(edge_id=f"e-{i}", tenant_id="t1", source_id="center", target_id=f"leaf-{i}", relationship_type="CONNECTS")
        for i in range(20)
    ]
    store.upsert_nodes(leaves, tenant_id="t1")
    store.upsert_edges(edges, tenant_id="t1")

    # Truncated traversal
    subgraph = store.traverse(
        start_node_ids=["center"],
        tenant_id="t1",
        max_nodes=10,
        max_edges=5,
        strict_limits=False,
    )
    assert subgraph.metadata["is_truncated"] is True
    assert len(subgraph.nodes) <= 10
    assert len(subgraph.edges) <= 5

    # Strict limit traversal
    with pytest.raises(GraphQueryError):
        store.traverse(
            start_node_ids=["center"],
            tenant_id="t1",
            max_nodes=10,
            max_edges=5,
            strict_limits=True,
        )


def test_explicit_max_edges_isolation():
    """Independently verifies max_edges limit enforcement when max_nodes is unconstrained."""
    store = InMemoryGraphStore()
    center = EntityNode(node_id="center", tenant_id="t1", entity_id="c", entity_type="hub", name="C", qualified_name="C")
    store.upsert_nodes([center], tenant_id="t1")

    # 15 leaf nodes with 15 edges
    leaves = [
        EntityNode(node_id=f"leaf-{i}", tenant_id="t1", entity_id=f"l{i}", entity_type="leaf", name=f"L{i}", qualified_name=f"L{i}")
        for i in range(15)
    ]
    edges = [
        RelationEdge(edge_id=f"e-{i}", tenant_id="t1", source_id="center", target_id=f"leaf-{i}", relationship_type="CONNECTS")
        for i in range(15)
    ]
    store.upsert_nodes(leaves, tenant_id="t1")
    store.upsert_edges(edges, tenant_id="t1")

    # 1. Relaxed mode: unconstrained max_nodes=1000, strict max_edges=5
    subgraph = store.traverse(
        start_node_ids=["center"],
        tenant_id="t1",
        max_nodes=1000,
        max_edges=5,
        strict_limits=False,
    )
    assert subgraph.metadata["is_truncated"] is True
    # Edge count must strictly equal max_edges (5)
    assert len(subgraph.edges) == 5
    # Node count is 6 (1 center + 5 connected leaves), well below max_nodes (1000)
    assert len(subgraph.nodes) == 6

    # 2. Strict mode: max_nodes=1000, max_edges=5 raises GraphQueryError explicitly citing edge limit
    with pytest.raises(GraphQueryError) as exc_info:
        store.traverse(
            start_node_ids=["center"],
            tenant_id="t1",
            max_nodes=1000,
            max_edges=5,
            strict_limits=True,
        )
    assert "edge limit" in str(exc_info.value).lower()

