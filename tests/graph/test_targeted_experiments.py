"""Comprehensive targeted experiment suite for Phase 2C edge cases.

Edge Cases Tested:
1. Extreme Delimiter & RFC-3986 Injective Key Collision Safety (symbols, slashes, colons, emojis)
2. Cyclic Multi-Hop Graph Traversal, Bounded Truncation & Determinism (BFS & DFS)
3. 5-Document Cascading Interleaved Lifecycle Reconciliation & Orphan Pruning
4. Hybrid RRF Mathematical Stress & Asymmetric Missing-Side Scaling
5. GraphContextAdapter Token Budget Stress & Citation Formatting Resilience
6. Serialization Validation under Complex Unicode & Cytoscape Element Integrity
"""

import hashlib
import json
import math
import urllib.parse
from typing import Dict, List, Optional, Set
import pytest

from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    GraphPath,
    canonical_entity_node_id,
    canonical_typed_node_id,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_relation_edge_id,
)
from md_generator.graph.exceptions import GraphQueryError, TenantBoundaryError
from md_generator.graph.stores.in_memory import InMemoryGraphStore
from md_generator.graph.hybrid.retriever import ScoredHybridResult
from md_generator.graph.hybrid.context import GraphContextAdapter
from md_generator.graph.serialization import (
    to_dict,
    to_json_ld,
    to_cytoscape,
    to_cypher_statements,
)
from md_generator.semantic.model.schema import SourceLocation


def compute_normalized_rrf(
    v_rank: Optional[int],
    g_rank: Optional[int],
    w_v: float = 1.0,
    w_g: float = 1.0,
    k: int = 60,
) -> float:
    if w_v < 0.0 or w_g < 0.0 or (w_v + w_g) <= 0.0:
        raise ValueError("Weights must be non-negative and sum to > 0.")
    rrf_max = (w_v / (k + 1)) + (w_g / (k + 1))
    rrf_raw = 0.0
    if v_rank is not None:
        rrf_raw += w_v / (k + v_rank)
    if g_rank is not None:
        rrf_raw += w_g / (k + g_rank)
    return min(1.0, max(0.0, rrf_raw / rrf_max)) if rrf_max > 0.0 else 0.0


def test_experiment_1_injective_key_collision():
    """Verifies RFC-3986 percent-encoding prevents key collision across complex delimiters."""
    tenant = "tenant:corp/alpha#1"
    
    tricky_ids = [
        "entity:1",
        "entity/1",
        "entity?1",
        "entity#1",
        "entity%201",
        "entity 1",
        "entity::1",
        "tenant:corp/alpha#1:entity:1",
        "a/b/c",
        "order.tax::calculate",
        "emoji_🚀_entity",
        "rel->to->target",
    ]
    
    keys = set()
    for tid in tricky_ids:
        key = canonical_entity_node_id(tenant, tid)
        assert key not in keys, f"Collision detected for {tid!r}: {key}"
        keys.add(key)
        prefix = f"tenant:{urllib.parse.quote(tenant, safe='')}:entity:"
        assert key.startswith(prefix)
        encoded_part = key[len(prefix):]
        decoded = urllib.parse.unquote(encoded_part)
        assert decoded == tid, f"Injective reversal failed for {tid!r}: got {decoded!r}"
    assert len(keys) == len(tricky_ids)


def test_experiment_2_cyclic_traversal_and_resource_limits():
    """Verifies cyclic graph traversals terminate cleanly in BFS/DFS with strict and graceful limits."""
    store = InMemoryGraphStore()
    tenant = "tenant-prod"
    
    nodes = [
        EntityNode(node_id=f"n-{x}", tenant_id=tenant, entity_id=f"e-{x}", entity_type="class", name=x, qualified_name=f"p.{x}")
        for x in ["A", "B", "C", "D", "E"]
    ]
    store.upsert_nodes(nodes, tenant_id=tenant)
    
    edges = [
        RelationEdge(edge_id="e-ab", tenant_id=tenant, source_id="n-A", target_id="n-B", relationship_type="CALLS", weight=0.9),
        RelationEdge(edge_id="e-bc", tenant_id=tenant, source_id="n-B", target_id="n-C", relationship_type="CALLS", weight=0.8),
        RelationEdge(edge_id="e-cd", tenant_id=tenant, source_id="n-C", target_id="n-D", relationship_type="CALLS", weight=0.7),
        RelationEdge(edge_id="e-da", tenant_id=tenant, source_id="n-D", target_id="n-A", relationship_type="CALLS", weight=0.6),
        RelationEdge(edge_id="e-be", tenant_id=tenant, source_id="n-B", target_id="n-E", relationship_type="USES", weight=0.5),
        RelationEdge(edge_id="e-cc", tenant_id=tenant, source_id="n-C", target_id="n-C", relationship_type="SELF_CALL", weight=1.0),
    ]
    store.upsert_edges(edges, tenant_id=tenant)
    
    # BFS
    kg_bfs = store.traverse(start_node_ids=["n-A"], tenant_id=tenant, max_depth=4, strategy="bfs")
    assert len(kg_bfs.nodes) == 5
    assert not kg_bfs.metadata.get("is_truncated", False)
    
    # DFS
    kg_dfs = store.traverse(start_node_ids=["n-A"], tenant_id=tenant, max_depth=4, strategy="dfs")
    assert len(kg_dfs.nodes) == 5
    
    # Strict limit exceeded
    with pytest.raises(GraphQueryError) as exc_info:
        store.traverse(start_node_ids=["n-A"], tenant_id=tenant, max_depth=4, max_nodes=3, strict_limits=True)
    assert "exceeded" in str(exc_info.value).lower()
        
    # Graceful truncation
    kg_trunc = store.traverse(start_node_ids=["n-A"], tenant_id=tenant, max_depth=4, max_nodes=3, strict_limits=False)
    assert len(kg_trunc.nodes) <= 3
    assert kg_trunc.metadata.get("is_truncated") is True


def test_experiment_3_cascading_interleaved_reconciliation():
    """Verifies interleaved multi-document deletion purges shared entities and edges without orphans."""
    store = InMemoryGraphStore()
    tenant = "tenant-lifecycle"
    
    doc_nodes = [
        EntityNode(node_id=canonical_document_node_id(tenant, f"D{i}"), tenant_id=tenant, entity_id=f"D{i}", entity_type="document", name=f"D{i}", qualified_name=f"doc.{i}", document_ids=[f"D{i}"])
        for i in range(1, 6)
    ]
    e1 = EntityNode(node_id="n-E1", tenant_id=tenant, entity_id="E1", entity_type="class", name="E1", qualified_name="p.E1", document_ids=["D1", "D2", "D3"], chunk_ids=["c1", "c2", "c3"])
    e2 = EntityNode(node_id="n-E2", tenant_id=tenant, entity_id="E2", entity_type="class", name="E2", qualified_name="p.E2", document_ids=["D2", "D4"], chunk_ids=["c2", "c4"])
    e3 = EntityNode(node_id="n-E3", tenant_id=tenant, entity_id="E3", entity_type="class", name="E3", qualified_name="p.E3", document_ids=["D3", "D4", "D5"], chunk_ids=["c3", "c4", "c5"])
    
    chunk_nodes = [
        EntityNode(node_id=canonical_chunk_node_id(tenant, f"c{i}"), tenant_id=tenant, entity_id=f"c{i}", entity_type="chunk", name=f"c{i}", qualified_name=f"chunk.{i}", document_ids=[f"D{i}"], chunk_ids=[f"c{i}"])
        for i in range(1, 6)
    ]
    store.upsert_nodes(doc_nodes + chunk_nodes + [e1, e2, e3], tenant_id=tenant)
    
    edge_12 = RelationEdge(edge_id="e-12", tenant_id=tenant, source_id="n-E1", target_id="n-E2", relationship_type="CALLS", weight=0.9, document_ids=["D2"], provenance=[EdgeProvenance(document_id="D2", confidence=0.9)])
    edge_23 = RelationEdge(edge_id="e-23", tenant_id=tenant, source_id="n-E2", target_id="n-E3", relationship_type="CALLS", weight=0.8, document_ids=["D4"], provenance=[EdgeProvenance(document_id="D4", confidence=0.8)])
    edge_13 = RelationEdge(edge_id="e-13", tenant_id=tenant, source_id="n-E1", target_id="n-E3", relationship_type="CALLS", weight=0.7, document_ids=["D3"], provenance=[EdgeProvenance(document_id="D3", confidence=0.7)])
    store.upsert_edges([edge_12, edge_23, edge_13], tenant_id=tenant)
    
    # Step 1: Delete D2
    store.delete_by_document("D2", tenant_id=tenant)
    nbrs = store.get_neighbors("n-E1", tenant_id=tenant, relationship_types=["CALLS"])
    assert len(nbrs) == 1
    assert nbrs[0][0].edge_id == "e-13"
    
    surv_e1 = store.get_node("n-E1", tenant_id=tenant)
    assert surv_e1 is not None
    assert surv_e1.document_ids == ["D1", "D3"]
    assert "c2" not in surv_e1.chunk_ids
    
    surv_e2 = store.get_node("n-E2", tenant_id=tenant)
    assert surv_e2 is not None
    assert surv_e2.document_ids == ["D4"]
    assert "c2" not in surv_e2.chunk_ids
    
    # Step 2: Delete D4
    store.delete_by_document("D4", tenant_id=tenant)
    assert store.get_node("n-E2", tenant_id=tenant) is None
    
    # Step 3: Delete D1, D3, D5
    store.delete_by_document("D1", tenant_id=tenant)
    store.delete_by_document("D3", tenant_id=tenant)
    store.delete_by_document("D5", tenant_id=tenant)
    
    assert store.get_node("n-E1", tenant_id=tenant) is None
    assert store.get_node("n-E3", tenant_id=tenant) is None
    for i in range(1, 6):
        assert store.get_node(canonical_document_node_id(tenant, f"D{i}"), tenant_id=tenant) is None
        assert store.get_node(canonical_chunk_node_id(tenant, f"c{i}"), tenant_id=tenant) is None


def test_experiment_4_rrf_asymmetric_stress():
    """Verifies normalized RRF scores monotonically in [0.0, 1.0] across asymmetric rank lists."""
    v_ranks = {f"doc_{i}": i + 1 for i in range(100)}
    g_ranks = {f"doc_{i}": i + 1 for i in [0, 10, 20, 30, 40]}
    
    scores = {}
    for doc_id in v_ranks:
        vr = v_ranks.get(doc_id)
        gr = g_ranks.get(doc_id)
        score = compute_normalized_rrf(vr, gr, w_v=1.0, w_g=1.0, k=60)
        assert 0.0 <= score <= 1.0, f"Score out of bounds: {score}"
        scores[doc_id] = score
        
    assert scores["doc_0"] == max(scores.values())
    assert scores["doc_0"] == 1.0
    assert scores["doc_10"] > scores["doc_1"]
    
    score_pure_v = compute_normalized_rrf(1, 1, w_v=1.0, w_g=0.0, k=60)
    assert score_pure_v == 1.0
    score_pure_g = compute_normalized_rrf(1, 1, w_v=0.0, w_g=1.0, k=60)
    assert score_pure_g == 1.0
    
    with pytest.raises(ValueError):
        compute_normalized_rrf(1, 1, w_v=0.0, w_g=0.0, k=60)


def test_experiment_5_context_adapter_token_budget_stress():
    """Verifies GraphContextAdapter enforces tight token budgets without truncating graph citations."""
    from md_generator.adapters.langchain.context import PromptContextBuilder
    
    builder = PromptContextBuilder(max_tokens=60, include_citations=True)
    adapter = GraphContextAdapter(context_builder=builder)
    
    loc = SourceLocation(location_type="code", path="src/core.py", line_start=15, line_end=45)
    results = [
        ScoredHybridResult(
            chunk_id="c1",
            content="Short sentence A.",
            tenant_id="t1",
            vector_score=0.9,
            graph_score=0.9,
            hybrid_score=0.9,
            provenance="HYBRID",
            metadata={"document_id": "d1", "chunk_id": "c1", "source_location": loc.to_dict()},
            graph_paths=[
                GraphPath(seed_chunk_id="c1", target_node_id="target_A", node_ids=["c1", "tA"], edge_ids=["e1"], depth=1, score=0.9)
            ],
        ),
        ScoredHybridResult(
            chunk_id="c2",
            content="Second chunk content B that is slightly longer.",
            tenant_id="t1",
            vector_score=0.8,
            graph_score=0.7,
            hybrid_score=0.75,
            provenance="HYBRID",
            metadata={"document_id": "d2", "chunk_id": "c2"},
            graph_paths=[],
        ),
        ScoredHybridResult(
            chunk_id="c3",
            content="Third chunk C that should be truncated by budget.",
            tenant_id="t1",
            vector_score=0.5,
            graph_score=0.4,
            hybrid_score=0.45,
            provenance="HYBRID",
            metadata={"document_id": "d3", "chunk_id": "c3"},
            graph_paths=[],
        ),
    ]
    
    context = adapter.build_context(results)
    assert "[Graph Path" in context
    assert "src/core.py:15-45" in context
    assert "Third chunk C" not in context


def test_experiment_6_complex_serialization_integrity():
    """Verifies serialization integrity under complex unicode, cyclic topologies, and Cytoscape export."""
    tenant = "t_audit"
    nodes = {
        f"n-{i}": EntityNode(
            node_id=f"n-{i}",
            tenant_id=tenant,
            entity_id=f"ent_{i}",
            entity_type="table",
            name=f"テーブル_{i}",
            qualified_name=f"schema.table_{i}",
            properties={"index_count": i, "is_partitioned": i % 2 == 0, "null_field": None},
        )
        for i in range(20)
    }
    edges = {
        f"e-{i}": RelationEdge(
            edge_id=f"e-{i}",
            tenant_id=tenant,
            source_id=f"n-{i % 20}",
            target_id=f"n-{(i + 1) % 20}",
            relationship_type="FOREIGN_KEY",
            weight=1.0 / (i + 1),
            document_ids=["doc-audit"],
            provenance=[EdgeProvenance(document_id="doc-audit", confidence=1.0 / (i + 1))],
        )
        for i in range(30)
    }
    kg = KnowledgeGraph(tenant_id=tenant, nodes=nodes, edges=edges)
    
    json_ld = to_json_ld(kg, include_tenant=False)
    dumped = json.dumps(json_ld, ensure_ascii=False)
    parsed = json.loads(dumped)
    assert len(parsed["@graph"]["nodes"]) == 20
    assert len(parsed["@graph"]["edges"]) == 30
    assert parsed["@context"]["kg"] == "https://mdengine.dev/ontology#"
    assert "tenantId" not in parsed
    
    cy = to_cytoscape(kg)
    node_ids = {n["data"]["id"] for n in cy["elements"]["nodes"]}
    for edge in cy["elements"]["edges"]:
        src = edge["data"]["source"]
        tgt = edge["data"]["target"]
        assert src in node_ids, f"Cytoscape edge source {src} not found in nodes"
        assert tgt in node_ids, f"Cytoscape edge target {tgt} not found in nodes"
        
    cypher_stmts = to_cypher_statements(kg)
    assert len(cypher_stmts) == 50
