import pytest

from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.graph.model import EntityNode, RelationEdge, KnowledgeGraph
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_cross_tenant_edge_rejection():
    store = InMemoryGraphStore()
    node_a = EntityNode(
        node_id="n-a", tenant_id="tenant-A", entity_id="ea", entity_type="class", name="A", qualified_name="a.A"
    )
    store.upsert_nodes([node_a], tenant_id="tenant-A")

    edge_b = RelationEdge(
        edge_id="e-ab", tenant_id="tenant-B", source_id="n-a", target_id="n-b", relationship_type="USES"
    )
    # Attempting to upsert edge with mismatched operation tenant raises TenantBoundaryError
    with pytest.raises(TenantBoundaryError):
        store.upsert_edges([edge_b], tenant_id="tenant-A")


def test_tenant_data_isolation():
    store = InMemoryGraphStore()
    node_a = EntityNode(
        node_id="shared-id", tenant_id="tenant-A", entity_id="ea", entity_type="class", name="A", qualified_name="a.A"
    )
    node_b = EntityNode(
        node_id="shared-id", tenant_id="tenant-B", entity_id="eb", entity_type="class", name="B", qualified_name="b.B"
    )

    store.upsert_nodes([node_a], tenant_id="tenant-A")
    store.upsert_nodes([node_b], tenant_id="tenant-B")

    retrieved_a = store.get_node("shared-id", tenant_id="tenant-A")
    retrieved_b = store.get_node("shared-id", tenant_id="tenant-B")

    assert retrieved_a is not None and retrieved_a.name == "A"
    assert retrieved_b is not None and retrieved_b.name == "B"

    # Traversal in tenant-A does not see tenant-B
    traversed_a = store.traverse(start_node_ids=["shared-id"], tenant_id="tenant-A")
    assert "shared-id" in traversed_a.nodes
    assert traversed_a.nodes["shared-id"].name == "A"


def test_missing_or_invalid_tenant_rejected():
    store = InMemoryGraphStore()
    with pytest.raises(TenantBoundaryError):
        store.get_node("n-1", tenant_id="")
    with pytest.raises(TenantBoundaryError):
        store.get_node("n-1", tenant_id="   ")
    with pytest.raises(TenantBoundaryError):
        store.traverse(start_node_ids=["n-1"], tenant_id="")
    with pytest.raises(TenantBoundaryError):
        store.delete_by_tenant(tenant_id="")
