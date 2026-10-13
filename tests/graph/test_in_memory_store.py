import pytest

from md_generator.graph.model import EntityNode, RelationEdge, KnowledgeGraph
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_in_memory_crud_and_contains():
    store = InMemoryGraphStore()
    store.initialize()
    assert store.health_check() is True

    node1 = EntityNode(
        node_id="n-1", tenant_id="t1", entity_id="e1", entity_type="class", name="A", qualified_name="a.A"
    )
    node2 = EntityNode(
        node_id="n-2", tenant_id="t1", entity_id="e2", entity_type="class", name="B", qualified_name="b.B"
    )
    edge1 = RelationEdge(
        edge_id="e-1", tenant_id="t1", source_id="n-1", target_id="n-2", relationship_type="EXTENDS"
    )

    store.upsert_nodes([node1, node2], tenant_id="t1")
    store.upsert_edges([edge1], tenant_id="t1")

    assert store.get_node("n-1", tenant_id="t1") is not None
    assert store.get_node("n-unknown", tenant_id="t1") is None
    assert store.contains_nodes(["n-1", "n-2", "n-3"], tenant_id="t1") == {"n-1", "n-2"}


def test_in_memory_neighbors_directions():
    store = InMemoryGraphStore()
    node1 = EntityNode(node_id="n-1", tenant_id="t1", entity_id="e1", entity_type="fn", name="1", qualified_name="1")
    node2 = EntityNode(node_id="n-2", tenant_id="t1", entity_id="e2", entity_type="fn", name="2", qualified_name="2")
    node3 = EntityNode(node_id="n-3", tenant_id="t1", entity_id="e3", entity_type="fn", name="3", qualified_name="3")
    store.upsert_nodes([node1, node2, node3], tenant_id="t1")

    # n1 -> n2, n3 -> n1
    e1 = RelationEdge(edge_id="e-1", tenant_id="t1", source_id="n-1", target_id="n-2", relationship_type="CALLS")
    e2 = RelationEdge(edge_id="e-2", tenant_id="t1", source_id="n-3", target_id="n-1", relationship_type="CALLS")
    store.upsert_edges([e1, e2], tenant_id="t1")

    out_nbrs = store.get_neighbors("n-1", tenant_id="t1", direction="out")
    assert len(out_nbrs) == 1
    assert out_nbrs[0][1].node_id == "n-2"

    in_nbrs = store.get_neighbors("n-1", tenant_id="t1", direction="in")
    assert len(in_nbrs) == 1
    assert in_nbrs[0][1].node_id == "n-3"

    both_nbrs = store.get_neighbors("n-1", tenant_id="t1", direction="both")
    assert len(both_nbrs) == 2


def test_in_memory_traversal_cycle_detection():
    # Build cycle: n1 -> n2 -> n3 -> n1
    store = InMemoryGraphStore()
    nodes = [
        EntityNode(node_id=f"n-{i}", tenant_id="t1", entity_id=f"e{i}", entity_type="node", name=f"{i}", qualified_name=f"{i}")
        for i in range(1, 4)
    ]
    store.upsert_nodes(nodes, tenant_id="t1")

    edges = [
        RelationEdge(edge_id="e-12", tenant_id="t1", source_id="n-1", target_id="n-2", relationship_type="REL"),
        RelationEdge(edge_id="e-23", tenant_id="t1", source_id="n-2", target_id="n-3", relationship_type="REL"),
        RelationEdge(edge_id="e-31", tenant_id="t1", source_id="n-3", target_id="n-1", relationship_type="REL"),
    ]
    store.upsert_edges(edges, tenant_id="t1")

    # Traversing with depth 5 should terminate without infinite loop and collect all 3 nodes
    subgraph = store.traverse(start_node_ids=["n-1"], tenant_id="t1", max_depth=5, strategy="bfs")
    assert len(subgraph.nodes) == 3
    assert len(subgraph.edges) == 3

    # DFS strategy
    subgraph_dfs = store.traverse(start_node_ids=["n-1"], tenant_id="t1", max_depth=5, strategy="dfs")
    assert len(subgraph_dfs.nodes) == 3
    assert len(subgraph_dfs.edges) == 3
