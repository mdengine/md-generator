"""Deep Edge Cases Part 3: Neo4j Tenant Purge, Multi-Type Traversal, Clamping, and Zero-Result Fusions.

Scenarios Examined:
1. Multi-Tenant Cross-Contamination & delete_by_tenant Isolation
2. In-Memory Directional Neighbor Filtering & Regex Safety
3. Path Maximization & Topological Tie-Breaking (Superior 2-hop 0.30 path wins over 0.25 direct path)
4. Total Zero-Result Hybrid Fusion (Graceful empty returns without division-by-zero)
5. Context Adapter include_graph_paths=False Toggle & 1-Node Path Skipping
6. KnowledgeGraph to_dict/from_dict Roundtrip Equality & C15 JSON-LD Tenant Privacy
"""

from unittest.mock import MagicMock
import hashlib
import json
import math
import pytest

from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    GraphPath,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_entity_node_id,
    canonical_relation_edge_id,
)
from md_generator.graph.exceptions import (
    GraphError,
    GraphQueryError,
    TenantBoundaryError,
)
from md_generator.graph.stores.in_memory import InMemoryGraphStore
from md_generator.graph.hybrid.retriever import (
    HybridGraphRAGRetriever,
    ScoredHybridResult,
)
from md_generator.graph.hybrid.context import GraphContextAdapter
from md_generator.graph.serialization import (
    to_dict,
    to_json_ld,
    to_cytoscape,
    to_cypher_statements,
)
from md_generator.adapters.langchain.context import PromptContextBuilder


def test_tenant_purge_and_contains_isolation():
    """Verifies delete_by_tenant purges strictly target tenant and contains_nodes is isolated."""
    store = InMemoryGraphStore()
    
    # Populate Tenant A
    n_a1 = EntityNode(node_id="tA:n1", tenant_id="tenant-A", entity_id="e1", entity_type="class", name="SharedName", qualified_name="p.SharedName")
    n_a2 = EntityNode(node_id="tA:n2", tenant_id="tenant-A", entity_id="e2", entity_type="class", name="NodeA2", qualified_name="p.NodeA2")
    edge_a = RelationEdge(edge_id="tA:e1", tenant_id="tenant-A", source_id="tA:n1", target_id="tA:n2", relationship_type="CALLS", weight=0.9)
    store.upsert_nodes([n_a1, n_a2], tenant_id="tenant-A")
    store.upsert_edges([edge_a], tenant_id="tenant-A")
    
    # Populate Tenant B with identical local entity IDs
    n_b1 = EntityNode(node_id="tB:n1", tenant_id="tenant-B", entity_id="e1", entity_type="class", name="SharedName", qualified_name="p.SharedName")
    edge_b = RelationEdge(edge_id="tB:e1", tenant_id="tenant-B", source_id="tB:n1", target_id="tB:n1", relationship_type="SELF_CALL", weight=1.0)
    store.upsert_nodes([n_b1], tenant_id="tenant-B")
    store.upsert_edges([edge_b], tenant_id="tenant-B")
    
    # contains_nodes scoping
    found_a = store.contains_nodes(["tA:n1", "tB:n1"], tenant_id="tenant-A")
    assert found_a == {"tA:n1"}, f"Expected only tA:n1 for tenant-A, got {found_a}"
    found_b = store.contains_nodes(["tA:n1", "tB:n1"], tenant_id="tenant-B")
    assert found_b == {"tB:n1"}, f"Expected only tB:n1 for tenant-B, got {found_b}"
    
    # Empty list
    assert store.contains_nodes([], tenant_id="tenant-A") == set()
    
    # Purge Tenant A
    purged_cnt = store.delete_by_tenant("tenant-A")
    assert purged_cnt >= 2
    
    # Verify Tenant A is 100% empty
    assert store.get_node("tA:n1", tenant_id="tenant-A") is None
    assert store.get_node("tA:n2", tenant_id="tenant-A") is None
    assert store.contains_nodes(["tA:n1"], tenant_id="tenant-A") == set()
    
    # Verify Tenant B is 100% untouched
    surv_b = store.get_node("tB:n1", tenant_id="tenant-B")
    assert surv_b is not None
    assert surv_b.name == "SharedName"
    assert store.contains_nodes(["tB:n1"], tenant_id="tenant-B") == {"tB:n1"}


def test_directional_filtering_and_regex_safety():
    """Verifies directional filtering ('in', 'out', 'both') and type whitelisting."""
    store = InMemoryGraphStore()
    tenant = "tenant-dir"
    
    n_center = EntityNode(node_id="n-center", tenant_id=tenant, entity_id="center", entity_type="class", name="Center", qualified_name="p.Center")
    n_in = EntityNode(node_id="n-in", tenant_id=tenant, entity_id="in", entity_type="class", name="InCaller", qualified_name="p.InCaller")
    n_out = EntityNode(node_id="n-out", tenant_id=tenant, entity_id="out", entity_type="class", name="OutCallee", qualified_name="p.OutCallee")
    store.upsert_nodes([n_center, n_in, n_out], tenant_id=tenant)
    
    # n-in -> n-center (CALLS)
    e_in = RelationEdge(edge_id="e-in", tenant_id=tenant, source_id="n-in", target_id="n-center", relationship_type="CALLS", weight=0.9)
    # n-center -> n-out (EXTENDS)
    e_out = RelationEdge(edge_id="e-out", tenant_id=tenant, source_id="n-center", target_id="n-out", relationship_type="EXTENDS", weight=0.8)
    store.upsert_edges([e_in, e_out], tenant_id=tenant)
    
    # Direction 'out' from center -> should return e_out only
    nbrs_out = store.get_neighbors("n-center", tenant_id=tenant, direction="out")
    assert len(nbrs_out) == 1
    assert nbrs_out[0][0].edge_id == "e-out"
    assert nbrs_out[0][1].node_id == "n-out"
    
    # Direction 'in' from center -> should return e_in only
    nbrs_in = store.get_neighbors("n-center", tenant_id=tenant, direction="in")
    assert len(nbrs_in) == 1
    assert nbrs_in[0][0].edge_id == "e-in"
    assert nbrs_in[0][1].node_id == "n-in"
    
    # Direction 'both' -> should return both
    nbrs_both = store.get_neighbors("n-center", tenant_id=tenant, direction="both")
    assert len(nbrs_both) == 2
    
    # Filter by type 'CALLS' with direction 'both' -> only e_in
    nbrs_calls = store.get_neighbors("n-center", tenant_id=tenant, direction="both", relationship_types=["CALLS"])
    assert len(nbrs_calls) == 1
    assert nbrs_calls[0][0].edge_id == "e-in"
    
    # In-memory store filter with non-matching type returns empty
    assert store.get_neighbors("n-center", tenant_id=tenant, relationship_types=["NON_EXISTENT"]) == []

    # Neo4jGraphStore strictly validates regex on relationship_types
    from md_generator.graph.stores.neo4j import Neo4jGraphStore
    mock_driver = MagicMock()
    neo_store = Neo4jGraphStore(driver=mock_driver)
    with pytest.raises(GraphQueryError):
        neo_store.get_neighbors("n-center", tenant_id=tenant, relationship_types=["CALLS; DROP"])


def test_path_score_maximization():
    """Verifies C13 path scoring selects superior multi-hop path (0.30 > 0.25)."""
    # Subgraph:
    # Seed Chunk c1 -> nA (weight 0.5, len=1) -> S_g = 1/(1+1) * 0.5 = 0.25
    # Seed Chunk c1 -> nB (weight 1.0) -> nA (weight 0.9) (len=2, min_w=0.9) -> S_g = 1/(1+2) * 0.9 = 0.30
    store = InMemoryGraphStore()
    tenant = "tenant-path"
    
    c1 = EntityNode(node_id="c1", tenant_id=tenant, entity_id="c1", entity_type="chunk", name="c1", qualified_name="chunk.1")
    nA = EntityNode(node_id="nA", tenant_id=tenant, entity_id="nA", entity_type="class", name="A", qualified_name="p.A")
    nB = EntityNode(node_id="nB", tenant_id=tenant, entity_id="nB", entity_type="class", name="B", qualified_name="p.B")
    store.upsert_nodes([c1, nA, nB], tenant_id=tenant)
    
    # Path 1: direct edge c1 -> nA (w=0.5)
    e1 = RelationEdge(edge_id="e1", tenant_id=tenant, source_id="c1", target_id="nA", relationship_type="CALLS", weight=0.5)
    # Path 2: indirect c1 -> nB (w=1.0) and nB -> nA (w=0.9)
    e2 = RelationEdge(edge_id="e2", tenant_id=tenant, source_id="c1", target_id="nB", relationship_type="CALLS", weight=1.0)
    e3 = RelationEdge(edge_id="e3", tenant_id=tenant, source_id="nB", target_id="nA", relationship_type="CALLS", weight=0.9)
    store.upsert_edges([e1, e2, e3], tenant_id=tenant)
    
    mock_vec = MagicMock()
    mock_vec.tenant_id = tenant
    mock_vec.invoke.return_value = []
    
    retriever = HybridGraphRAGRetriever(
        vector_retriever=mock_vec,
        graph_store=store,
        tenant_id=tenant,
        top_k=5,
        max_depth=2,
    )
    
    # Reconstruct paths for subgraph
    sg = store.traverse(["c1"], tenant_id=tenant, max_depth=2)
    scores = retriever._reconstruct_paths_and_scores(sg, {"c1": "c1"})
    
    # In C13 path scoring, candidate nA evaluates all valid paths:
    # Path 1: depth 1, weight 0.5 -> score = 0.25
    # Path 2: depth 2, min weight 0.9 -> score = 0.30
    # Max score is 0.30!
    score_nA, paths_nA = scores["nA"]
    assert math.isclose(score_nA, 0.30, rel_tol=1e-3), f"Expected 0.30, got {score_nA}"
    assert len(paths_nA) == 2
    assert paths_nA[0].depth == 2
    assert math.isclose(paths_nA[0].score, 0.30, rel_tol=1e-3)
    
    # When two seeds reach nA at depth 1 with weights 0.2 and 0.8: max is selected!
    c2 = EntityNode(node_id="c2", tenant_id=tenant, entity_id="c2", entity_type="chunk", name="c2", qualified_name="chunk.2")
    store.upsert_nodes([c2], tenant_id=tenant)
    e_c2_nA = RelationEdge(edge_id="e-c2-a", tenant_id=tenant, source_id="c2", target_id="nA", relationship_type="CALLS", weight=0.8)
    store.upsert_edges([e_c2_nA], tenant_id=tenant)
    
    sg2 = store.traverse(["c1", "c2"], tenant_id=tenant, max_depth=1)
    scores2 = retriever._reconstruct_paths_and_scores(sg2, {"c1": "c1", "c2": "c2"})
    # Seed 1 gives 1/(1+1)*0.5 = 0.25; Seed 2 gives 1/(1+1)*0.8 = 0.40 -> max is 0.40!
    score_multi, paths_multi = scores2["nA"]
    assert math.isclose(score_multi, 0.40, rel_tol=1e-3), f"Expected 0.40, got {score_multi}"


def test_zero_result_hybrid_fusion():
    """Verifies hybrid retriever handles total zero results without division by zero."""
    store = InMemoryGraphStore()
    tenant = "tenant-zero"
    
    mock_vec = MagicMock()
    mock_vec.tenant_id = tenant
    mock_vec.invoke.return_value = []  # 0 vector candidates
    
    # Both fusion modes: RRF and linear
    for f_mode in ["rrf", "linear"]:
        retriever = HybridGraphRAGRetriever(
            vector_retriever=mock_vec,
            graph_store=store,
            tenant_id=tenant,
            top_k=10,
            fusion_mode=f_mode,  # type: ignore
        )
        res = retriever.retrieve("query returning nothing")
        assert res == [], f"Expected empty list for {f_mode}, got {res}"
        
        docs = retriever.invoke("query returning nothing")
        assert docs == []


def test_context_adapter_toggles_and_1node_paths():
    """Verifies include_graph_paths toggle and single-node path formatting omission."""
    builder = PromptContextBuilder(max_tokens=2000, include_citations=True)
    
    # 1. include_graph_paths=False
    adapter_no_graph = GraphContextAdapter(context_builder=builder, include_graph_paths=False)
    
    res = ScoredHybridResult(
        chunk_id="c1",
        content="Document content here.",
        tenant_id="t1",
        vector_score=0.9,
        graph_score=0.8,
        hybrid_score=0.85,
        provenance="HYBRID",
        metadata={"document_id": "d1", "chunk_id": "c1"},
        graph_paths=[GraphPath(seed_chunk_id="c1", target_node_id="t1", node_ids=["c1", "t1"], edge_ids=["e1"], depth=1, score=0.8)],
    )
    
    ctx_no_graph = adapter_no_graph.build_context([res])
    assert "--- Graph Relationships ---" not in ctx_no_graph
    assert "Document content here." in ctx_no_graph
    
    # 2. Single-node path (depth 0, len(node_ids) == 1) should be skipped in formatting
    adapter_with_graph = GraphContextAdapter(context_builder=builder, include_graph_paths=True)
    single_node_path = GraphPath(seed_chunk_id="c1", target_node_id="c1", node_ids=["c1"], edge_ids=[], depth=0, score=1.0)
    formatted = adapter_with_graph.format_graph_paths([single_node_path])
    assert formatted == "", f"Single node path should not format into arrows, got: {formatted!r}"


def test_serialization_roundtrip_and_cypher_properties():
    """Verifies KnowledgeGraph roundtrip equality, C15 JSON-LD tenant privacy, and Cypher syntax."""
    tenant = "t_rt"
    n = EntityNode(
        node_id="tenant:t_rt:entity:cls_user",
        tenant_id=tenant,
        entity_id="cls_user",
        entity_type="class",
        name="User",
        qualified_name="auth.User",
        properties={"role": "admin", "active": True, "attempts": 3},
    )
    e = RelationEdge(
        edge_id="tenant:t_rt:rel:user_self",
        tenant_id=tenant,
        source_id="tenant:t_rt:entity:cls_user",
        target_id="tenant:t_rt:entity:cls_user",
        relationship_type="SELF_REF",
        weight=0.95,
        properties={"ctx": "auth_flow"},
    )
    kg = KnowledgeGraph(tenant_id=tenant, nodes={n.node_id: n}, edges={e.edge_id: e})
    
    # 1. to_dict and full KnowledgeGraph reconstruction equality
    d = kg.to_dict()
    assert d["tenant_id"] == tenant
    assert n.node_id in d["nodes"]
    assert e.edge_id in d["edges"]
    assert d["nodes"][n.node_id]["properties"]["role"] == "admin"

    kg_recon = KnowledgeGraph.from_dict(d)
    assert kg_recon == kg
    assert kg_recon.tenant_id == kg.tenant_id
    assert kg_recon.nodes == kg.nodes
    assert kg_recon.edges == kg.edges
    assert kg_recon.to_dict() == d

    # 2. C15 JSON-LD tenant privacy (complete scrubbing of tenant)
    ld_private = to_json_ld(kg, include_tenant=False)
    assert "tenantId" not in ld_private
    assert "tenantId" not in ld_private["@graph"]["nodes"][0]
    assert "tenantId" not in ld_private["@graph"]["edges"][0]
    assert ld_private["@graph"]["nodes"][0]["@id"] == "entity:cls_user"
    assert ld_private["@graph"]["edges"][0]["source"] == "entity:cls_user"
    assert ld_private["@graph"]["edges"][0]["target"] == "entity:cls_user"
    assert tenant not in json.dumps(ld_private)
    
    # 3. to_cypher_statements (serializer formatting)
    stmts = to_cypher_statements(kg)
    assert len(stmts) == 2
    assert "MERGE (n:EntityNode" in stmts[0]
    assert "n.name = 'User'" in stmts[0]
    assert "MERGE (s)-[r:`SELF_REF`" in stmts[1]
