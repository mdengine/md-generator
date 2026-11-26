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


# ==============================================================================
# Prompt 05 Incremental Knowledge Graph & Reconciliation Acceptance Suite
# ==============================================================================

import concurrent.futures
import hashlib
from md_generator.graph.model import (
    canonical_page_node_id,
    canonical_slide_node_id,
    canonical_section_node_id,
    canonical_table_node_id,
    canonical_image_node_id,
    GraphTombstone,
    KnowledgeGraph,
)
from md_generator.graph.extractor import extract
from md_generator.graph.entity_extractor import RuleBasedEntityExtractor
from md_generator.graph.tombstone import TombstoneManager
from md_generator.graph.reconciler import (
    GraphReconciler,
    ReconciliationDiff,
    ReconciliationResult,
    compute_document_content_hash,
)
from md_generator.graph.exceptions import TenantBoundaryError, GraphStoreError
from md_generator.semantic.model.schema import (
    SemanticDocument,
    SemanticChunk,
    Entity,
    Relationship,
    SourceLocation,
    ChunkLineage,
)


def _make_sample_doc_and_chunks(doc_id_seed: str = "doc1"):
    doc_id = hashlib.sha256(doc_id_seed.encode("utf-8")).hexdigest()
    cid1 = hashlib.sha256(f"{doc_id_seed}-c1".encode("utf-8")).hexdigest()
    cid2 = hashlib.sha256(f"{doc_id_seed}-c2".encode("utf-8")).hexdigest()

    doc = SemanticDocument(
        document_id=doc_id,
        sanitized_content="Acme Corp announced that Dr. Alice Smith will lead the Project Titan in New York.",
    )

    c1 = SemanticChunk(
        chunk_id=cid1,
        document_id=doc_id,
        sanitized_content="Acme Corp is partnered with FinTech LLC in New York for Project Titan.",
        lineage=ChunkLineage(
            location=SourceLocation(location_type="pdf", path="/data/doc.pdf", page=1)
        ),
    )
    c2 = SemanticChunk(
        chunk_id=cid2,
        document_id=doc_id,
        sanitized_content="Financial results summary:\n| Quarter | Revenue |\n|:--- |:--- |\n| Q1 | $10M |\n",
        lineage=ChunkLineage(
            location=SourceLocation(location_type="pdf", path="/data/doc.pdf", page=2)
        ),
    )
    return doc, [c1, c2]


def test_structural_and_domain_node_creation():
    """Validates structural nodes (page, table) and domain nodes (org, person, product, location)."""
    doc, chunks = _make_sample_doc_and_chunks("test-struct")
    tenant = "tenant-struct"

    kg = extract(
        doc,
        chunks,
        tenant_id=tenant,
        extract_structural=True,
        extract_domain=True,
    )

    # 1. Structural node checks
    node_types = {n.entity_type for n in kg.nodes.values()}
    assert "document" in node_types
    assert "chunk" in node_types
    assert "page" in node_types
    assert "table" in node_types

    # 2. Page node identity check
    page1_nid = canonical_page_node_id(tenant, doc.document_id, 1)
    assert page1_nid in kg.nodes
    page1_node = kg.nodes[page1_nid]
    assert page1_node.properties["page"] == 1

    # 3. Structural edges: CONTAINS_PAGE, CONTAINS_TABLE
    rel_types = {e.relationship_type for e in kg.edges.values()}
    assert "CONTAINS_PAGE" in rel_types
    assert "CONTAINS_TABLE" in rel_types

    # 4. Domain entity nodes extracted by rule-based engine
    domain_types = {n.entity_type for n in kg.nodes.values() if n.entity_type not in ("document", "chunk", "page", "slide", "section", "table", "image")}
    assert "organization" in domain_types or "location" in domain_types


def test_incremental_reconciliation_initial_and_modify():
    """Validates initial ingestion, then modification of chunks with clean delta updates."""
    store = InMemoryGraphStore()
    tomb_mgr = TombstoneManager()
    reconciler = GraphReconciler(store=store, tombstone_manager=tomb_mgr)
    tenant = "tenant-reconcile"

    doc, chunks = _make_sample_doc_and_chunks("doc-lifecycle")

    # Initial ingestion
    res1 = reconciler.reconcile_document(doc, chunks, tenant_id=tenant, store=store)
    assert res1.unchanged is False
    assert len(res1.diff.inserted_nodes) > 0
    assert len(res1.diff.inserted_edges) > 0
    assert len(res1.diff.deleted_node_ids) == 0

    # Modify: replace chunk 2 with chunk 3
    cid3 = hashlib.sha256(b"chunk-3-brand-new").hexdigest()
    c3 = SemanticChunk(
        chunk_id=cid3,
        document_id=doc.document_id,
        sanitized_content="Brand new chunk 3 for Dr. Alice Smith.",
        lineage=ChunkLineage(
            location=SourceLocation(location_type="pdf", path="/data/doc.pdf", page=3)
        ),
    )
    modified_chunks = [chunks[0], c3]

    res2 = reconciler.reconcile_document(
        doc,
        modified_chunks,
        tenant_id=tenant,
        store=store,
        prev_content_hash=res1.current_hash,
    )

    assert res2.unchanged is False
    # Chunk 2 should be deleted
    c2_nid = canonical_chunk_node_id(tenant, chunks[1].chunk_id)
    assert c2_nid in res2.diff.deleted_node_ids
    # Chunk 3 should be inserted
    c3_nid = canonical_chunk_node_id(tenant, cid3)
    inserted_nids = [n.node_id for n in res2.diff.inserted_nodes]
    assert c3_nid in inserted_nids

    # Verify store state reflects the changes
    assert store.get_node(c2_nid, tenant_id=tenant) is None
    assert store.get_node(c3_nid, tenant_id=tenant) is not None


def test_idempotent_repeated_synchronization():
    """Validates that repeating synchronization with identical hash is an immediate no-op."""
    store = InMemoryGraphStore()
    reconciler = GraphReconciler(store=store)
    tenant = "tenant-idempotent"

    doc, chunks = _make_sample_doc_and_chunks("doc-idem")
    res1 = reconciler.reconcile_document(doc, chunks, tenant_id=tenant, store=store)
    assert res1.unchanged is False

    # Second run with same content and matching previous_hash
    res2 = reconciler.reconcile_document(
        doc,
        chunks,
        tenant_id=tenant,
        store=store,
        prev_content_hash=res1.current_hash,
    )
    assert res2.unchanged is True
    assert res2.diff.has_changes is False


def test_document_deletion_and_tombstones():
    """Validates that document deletion generates tombstones and purges graph data."""
    store = InMemoryGraphStore()
    tomb_mgr = TombstoneManager()
    reconciler = GraphReconciler(store=store, tombstone_manager=tomb_mgr)
    tenant = "tenant-delete"

    doc, chunks = _make_sample_doc_and_chunks("doc-tomb")
    reconciler.reconcile_document(doc, chunks, tenant_id=tenant, store=store)

    # Delete document
    del_res = reconciler.delete_document(doc.document_id, tenant_id=tenant, store=store)

    assert len(del_res.diff.tombstones) > 0
    # Tombstone for document must be recorded
    assert tomb_mgr.is_tombstoned(doc.document_id, tenant_id=tenant)
    for c in chunks:
        assert tomb_mgr.is_tombstoned(c.chunk_id, tenant_id=tenant)

    # Graph elements must be purged from store
    doc_nid = canonical_document_node_id(tenant, doc.document_id)
    assert store.get_node(doc_nid, tenant_id=tenant) is None


def test_crash_recovery_atomic_rollback():
    """Validates that a simulated failure during reconciliation safely rolls back store state."""
    class BrokenStore(InMemoryGraphStore):
        def upsert_edges(self, edges, tenant_id):
            raise RuntimeError("Simulated crash during edge upsert")

    broken_store = BrokenStore()
    reconciler = GraphReconciler()
    tenant = "tenant-crash"

    doc, chunks = _make_sample_doc_and_chunks("doc-crash")

    with pytest.raises(GraphStoreError, match="transaction failed"):
        reconciler.reconcile_document(doc, chunks, tenant_id=tenant, store=broken_store)

    # Store must remain empty and uncorrupted after rollback
    assert len(broken_store.get_all_nodes(tenant_id=tenant)) == 0


def test_tenant_isolation_in_reconciliation():
    """Validates that mismatched tenant IDs are strictly rejected."""
    store = InMemoryGraphStore()
    reconciler = GraphReconciler()
    doc, chunks = _make_sample_doc_and_chunks("doc-iso")

    with pytest.raises(TenantBoundaryError):
        reconciler.reconcile_document(doc, chunks, tenant_id="", store=store)
    with pytest.raises(TenantBoundaryError):
        reconciler.reconcile_document(doc, chunks, tenant_id="   ", store=store)


def test_concurrent_ingestion_thread_safety():
    """Validates that concurrent document reconciliations execute without race conditions."""
    store = InMemoryGraphStore()
    reconciler = GraphReconciler()
    tenant = "tenant-concurrent"

    def _reconcile_doc(idx: int):
        doc, chunks = _make_sample_doc_and_chunks(f"doc-thread-{idx}")
        res = reconciler.reconcile_document(doc, chunks, tenant_id=tenant, store=store)
        return res.unchanged is False

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_reconcile_doc, i) for i in range(8)]
        results = [f.result() for f in futures]

    assert all(results)
    # Total nodes in store should match all 8 documents ingested
    nodes = store.get_all_nodes(tenant_id=tenant)
    assert len(nodes) >= 8 * 2


def test_knowledge_graph_tombstone_serialization_compatibility():
    """Validates that KnowledgeGraph tombstones serialize cleanly to dict and JSON."""
    tenant = "tenant-serial"
    tomb = GraphTombstone(
        tenant_id=tenant,
        target_type="document",
        target_id="doc-123",
        timestamp=123456789.0,
        version_hash="abc",
    )
    kg = KnowledgeGraph(
        tenant_id=tenant,
        nodes={},
        edges={},
        tombstones={tomb.tombstone_id: tomb},
    )

    d = kg.to_dict()
    assert "tombstones" in d
    assert tomb.tombstone_id in d["tombstones"]

    reloaded = KnowledgeGraph.from_dict(d)
    assert len(reloaded.tombstones) == 1
    assert reloaded.tombstones[tomb.tombstone_id].target_id == "doc-123"

