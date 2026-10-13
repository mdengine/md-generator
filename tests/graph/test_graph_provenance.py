import pytest

from md_generator.graph.model import EntityNode, RelationEdge, EdgeProvenance, canonical_document_node_id
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_multi_document_edge_provenance_preservation():
    store = InMemoryGraphStore()
    tenant = "tenant-1"

    # 3 Documents and 2 Entities
    doc_nodes = [
        EntityNode(
            node_id=canonical_document_node_id(tenant, f"doc-{i}"),
            tenant_id=tenant,
            entity_id=f"doc-{i}",
            entity_type="document",
            name=f"doc-{i}",
            qualified_name=f"doc.{i}",
            document_ids=[f"doc-{i}"],
        )
        for i in range(1, 4)
    ]
    node_a = EntityNode(
        node_id="n-a",
        tenant_id=tenant,
        entity_id="ea",
        entity_type="class",
        name="A",
        qualified_name="a.A",
        document_ids=["doc-1", "doc-2", "doc-3"],
    )
    node_b = EntityNode(
        node_id="n-b",
        tenant_id=tenant,
        entity_id="eb",
        entity_type="class",
        name="B",
        qualified_name="b.B",
        document_ids=["doc-1", "doc-2", "doc-3"],
    )
    store.upsert_nodes(doc_nodes + [node_a, node_b], tenant_id=tenant)

    # Edge shared across 3 documents with different confidences
    edge = RelationEdge(
        edge_id="e-ab",
        tenant_id=tenant,
        source_id="n-a",
        target_id="n-b",
        relationship_type="CALLS",
        weight=0.95,
        document_ids=["doc-1", "doc-2", "doc-3"],
        provenance=[
            EdgeProvenance(document_id="doc-1", confidence=0.95),
            EdgeProvenance(document_id="doc-2", confidence=0.70),
            EdgeProvenance(document_id="doc-3", confidence=0.80),
        ],
    )
    store.upsert_edges([edge], tenant_id=tenant)

    # Delete doc-1
    purged = store.delete_by_document("doc-1", tenant_id=tenant)
    assert purged >= 1

    # Edge must survive!
    surviving_edges = store.get_neighbors("n-a", tenant_id=tenant, direction="out")
    assert len(surviving_edges) == 1
    surviving_edge = surviving_edges[0][0]

    assert "doc-1" not in surviving_edge.document_ids
    assert surviving_edge.document_ids == ["doc-2", "doc-3"]
    assert len(surviving_edge.provenance) == 2
    # New weight should be max of doc-2 (0.70) and doc-3 (0.80) = 0.80
    assert surviving_edge.weight == 0.80

    # Surviving nodes
    surviving_node_a = store.get_node("n-a", tenant_id=tenant)
    assert surviving_node_a is not None
    assert "doc-1" not in surviving_node_a.document_ids
    assert surviving_node_a.document_ids == ["doc-2", "doc-3"]
