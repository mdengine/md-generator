import pytest

from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    EdgeProvenance,
    canonical_chunk_node_id,
    canonical_document_node_id,
)
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_document_lifecycle_5step_reconciliation():
    store = InMemoryGraphStore()
    tenant = "tenant-1"

    # Doc 1 with chunk-1 and chunk-2
    doc1_node = EntityNode(
        node_id=canonical_document_node_id(tenant, "doc-1"),
        tenant_id=tenant,
        entity_id="doc-1",
        entity_type="document",
        name="doc-1",
        qualified_name="doc.1",
        document_ids=["doc-1"],
    )
    chunk1_node = EntityNode(
        node_id=canonical_chunk_node_id(tenant, "chunk-1"),
        tenant_id=tenant,
        entity_id="chunk-1",
        entity_type="chunk",
        name="c1",
        qualified_name="chunk.1",
        document_ids=["doc-1"],
        chunk_ids=["chunk-1"],
    )
    chunk2_node = EntityNode(
        node_id=canonical_chunk_node_id(tenant, "chunk-2"),
        tenant_id=tenant,
        entity_id="chunk-2",
        entity_type="chunk",
        name="c2",
        qualified_name="chunk.2",
        document_ids=["doc-1"],
        chunk_ids=["chunk-2"],
    )

    # Entity e1: owned solely by doc-1
    ent_sole = EntityNode(
        node_id="n-sole",
        tenant_id=tenant,
        entity_id="e-sole",
        entity_type="function",
        name="sole_fn",
        qualified_name="pkg.sole_fn",
        document_ids=["doc-1"],
        chunk_ids=["chunk-1"],
    )

    # Entity e2: shared between doc-1 and doc-2
    ent_shared = EntityNode(
        node_id="n-shared",
        tenant_id=tenant,
        entity_id="e-shared",
        entity_type="class",
        name="SharedClass",
        qualified_name="pkg.SharedClass",
        document_ids=["doc-1", "doc-2"],
        chunk_ids=["chunk-2", "chunk-other"],
    )

    store.upsert_nodes([doc1_node, chunk1_node, chunk2_node, ent_sole, ent_shared], tenant_id=tenant)

    # Edges
    edge1 = RelationEdge(
        edge_id="e-c1-sole",
        tenant_id=tenant,
        source_id=chunk1_node.node_id,
        target_id=ent_sole.node_id,
        relationship_type="CONTAINS_ENTITY",
        document_ids=["doc-1"],
        chunk_ids=["chunk-1"],
        provenance=[EdgeProvenance(document_id="doc-1", chunk_id="chunk-1")],
    )
    edge2 = RelationEdge(
        edge_id="e-sole-shared",
        tenant_id=tenant,
        source_id=ent_sole.node_id,
        target_id=ent_shared.node_id,
        relationship_type="CALLS",
        document_ids=["doc-1"],
        chunk_ids=["chunk-1"],
        provenance=[EdgeProvenance(document_id="doc-1", chunk_id="chunk-1")],
    )
    store.upsert_edges([edge1, edge2], tenant_id=tenant)

    # Execute 5-step reconciliation
    purged_count = store.delete_by_document("doc-1", tenant_id=tenant)
    assert purged_count > 0

    # 1. Chunk nodes must be gone
    assert store.get_node(chunk1_node.node_id, tenant_id=tenant) is None
    assert store.get_node(chunk2_node.node_id, tenant_id=tenant) is None

    # 2. Document node must be gone
    assert store.get_node(doc1_node.node_id, tenant_id=tenant) is None

    # 3. Sole entity must be deleted (orphaned)
    assert store.get_node(ent_sole.node_id, tenant_id=tenant) is None

    # 4. Shared entity must survive, but with doc-1 and chunk-2 removed!
    surviving_shared = store.get_node(ent_shared.node_id, tenant_id=tenant)
    assert surviving_shared is not None
    assert surviving_shared.document_ids == ["doc-2"]
    assert "chunk-2" not in surviving_shared.chunk_ids
    assert surviving_shared.chunk_ids == ["chunk-other"]

    # 5. Edges involving sole entity must be purged
    assert store.get_neighbors(ent_shared.node_id, tenant_id=tenant, direction="both") == []
