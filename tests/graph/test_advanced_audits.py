"""Advanced Phase 2C edge cases and stress audits suite.

Edge Cases Examined:
1. Neo4j Error Handling, Special Character Escaping & Rollback Resilience
2. Extractor Boundary Edge Cases (0-chunk doc & 100-chunk scale)
3. Hybrid Retriever Vector-Graph Disconnect & Fallback Handling
4. Context Adapter Multi-Path Pruning & Path Ordering
5. Serialization Empty & Self-Loop Edge Cases
"""

from unittest.mock import MagicMock
import hashlib
import json
import pytest

from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    GraphPath,
    canonical_chunk_node_id,
    canonical_document_node_id,
)
from md_generator.graph.exceptions import (
    GraphError,
    GraphStoreError,
    Neo4jDependencyError,
    TenantBoundaryError,
)
from md_generator.graph.protocol import GraphStore
from md_generator.graph.stores.in_memory import InMemoryGraphStore
from md_generator.graph.stores.neo4j import Neo4jGraphStore
from md_generator.graph.extractor import extract
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
from md_generator.semantic.model.schema import (
    SemanticDocument,
    SemanticChunk,
    Entity,
    Relationship,
    SourceLocation,
    ChunkLineage,
)


def hex_id(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def test_audit_1_neo4j_escaping_and_rollback():
    """Verifies Neo4j handles tricky character escaping in payloads and rolls back on failure."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    store = Neo4jGraphStore(driver=mock_driver)
    in_mem = InMemoryGraphStore()
    assert isinstance(store, GraphStore), "Neo4jGraphStore must implement GraphStore Protocol"
    assert isinstance(in_mem, GraphStore), "InMemoryGraphStore must implement GraphStore Protocol"
    
    tricky_props = {
        "query": "SELECT * FROM 'users' WHERE name = \"O'Reilly\\admin\";\n\t-- DROP",
        "nested": {"key": "val with \"quotes\" and \\escapes\\"},
        "unicode": "こんにちは世界 🚀",
        "multiline": "line1\nline2\r\nline3",
    }
    node = EntityNode(
        node_id="n-tricky",
        tenant_id="t1",
        entity_id="e-tricky",
        entity_type="query",
        name="TrickyQuery",
        qualified_name="pkg.TrickyQuery",
        properties=tricky_props,
    )
    mock_res = MagicMock()
    mock_res.single.return_value = {"cnt": 1}
    mock_session.run.return_value = mock_res
    
    count = store.upsert_nodes([node], tenant_id="t1")
    assert count == 1
    call_args = mock_session.run.call_args
    batch_item = call_args[1]["batch"][0]
    parsed_props = json.loads(batch_item["properties"])
    assert parsed_props["query"] == tricky_props["query"]
    assert parsed_props["unicode"] == tricky_props["unicode"]
    
    # Verify rollback on transaction failure
    mock_tx = MagicMock()
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
    res1 = MagicMock()
    res1.single.return_value = {"d_chunks": ["c1"], "purged_chunks": 1}
    mock_tx.run.side_effect = [res1, RuntimeError("Simulated Database Network Crash")]
    
    with pytest.raises(GraphStoreError) as exc_info:
        store.delete_by_document("doc-fail", tenant_id="t1")
    assert "Simulated Database Network Crash" in str(exc_info.value)
    assert not mock_tx.commit.called
    assert mock_tx.rollback.called


def test_audit_2_extractor_boundary_cases():
    """Verifies extractor handles 0-chunk boundary and 100-chunk deduplication cleanly."""
    tenant = "tenant-ext"
    doc_id = hex_id("doc-scale")
    
    # 1. Document with 0 chunks
    doc_empty_chunks = SemanticDocument(
        document_id=doc_id,
        sanitized_content="Document with no chunks.",
        entities=[Entity(entity_id=hex_id("e-doc"), entity_type="module", name="Mod", qualified_name="pkg.Mod")],
    )
    kg_empty = extract(doc_empty_chunks, [], tenant_id=tenant)
    assert len(kg_empty.nodes) == 2  # Document node + Entity node
    assert len(kg_empty.edges) == 0  # No chunks to anchor CONTAINS_CHUNK or CONTAINS_ENTITY edges
    
    # 2. 100 chunks stress test
    chunks_100 = []
    for i in range(100):
        c_id = hex_id(f"chunk-{i}")
        ent_hex = hex_id(f"ent-{i % 10}")
        ent = Entity(entity_id=ent_hex, entity_type="class", name=f"Class{i % 10}", qualified_name=f"p.Class{i % 10}")
        rel = Relationship(
            relationship_id=hex_id(f"rel-{i}"),
            source_entity_id=ent_hex,
            target_entity_id=hex_id(f"ent-{(i + 1) % 10}"),
            relationship_type="CALLS",
            confidence=0.8
        ) if i % 10 != 9 else None
        
        chunk = SemanticChunk(
            chunk_id=c_id,
            document_id=doc_id,
            sanitized_content=f"Content chunk {i}",
            entities=[ent],
            relationships=[rel] if rel else [],
        )
        chunks_100.append(chunk)
        
    kg_scale = extract(doc_empty_chunks, chunks_100, tenant_id=tenant)
    assert len(kg_scale.nodes) == 112
    for j in range(10):
        target_hex = hex_id(f"ent-{j}")
        e_node = next(n for n in kg_scale.nodes.values() if n.entity_id == target_hex)
        assert len(e_node.chunk_ids) == 10


def test_audit_3_hybrid_disconnect_and_tie_breaking():
    """Verifies graceful handling of vector candidates absent from graph and deterministic tie-breaking."""
    try:
        from langchain_core.documents import Document
    except ImportError:
        class Document:  # type: ignore[no-redef]
            def __init__(self, page_content: str, metadata: dict):
                self.page_content = page_content
                self.metadata = metadata
    mock_vec = MagicMock()
    mock_vec.tenant_id = "tenant-hybrid"
    
    mock_vec.invoke.return_value = [
        Document(page_content="Content 1", metadata={"chunk_id": "c1", "score": 0.85}),
        Document(page_content="Content 2", metadata={"chunk_id": "c2", "score": 0.85}),
        Document(page_content="Content 3", metadata={"chunk_id": "c3-orphan", "score": 0.90}),
    ]
    
    store = InMemoryGraphStore()
    tenant = "tenant-hybrid"
    c1_node = EntityNode(node_id=canonical_chunk_node_id(tenant, "c1"), tenant_id=tenant, entity_id="c1", entity_type="chunk", name="c1", qualified_name="chunk.1")
    c2_node = EntityNode(node_id=canonical_chunk_node_id(tenant, "c2"), tenant_id=tenant, entity_id="c2", entity_type="chunk", name="c2", qualified_name="chunk.2")
    store.upsert_nodes([c1_node, c2_node], tenant_id=tenant)
    
    retriever = HybridGraphRAGRetriever(
        vector_retriever=mock_vec,
        graph_store=store,
        tenant_id=tenant,
        top_k=5,
        fusion_mode="linear",
        alpha=0.5,
    )
    
    results = retriever.retrieve("test query")
    assert len(results) == 3
    
    res_map = {r.chunk_id: r for r in results}
    # Orphan vector candidate without graph node
    assert res_map["c3-orphan"].provenance == "VECTOR_ONLY"
    assert res_map["c3-orphan"].graph_score == 0.0
    assert res_map["c3-orphan"].hybrid_score == 0.5 * 0.90
    
    # Candidates in both vector and graph
    assert res_map["c1"].provenance == "HYBRID"
    assert res_map["c1"].graph_score == 1.0
    assert res_map["c1"].hybrid_score == (0.5 * 0.85) + (0.5 * 1.0)
    
    # Deterministic tie-breaking by chunk_id
    assert results[0].chunk_id == "c1"
    assert results[1].chunk_id == "c2"


def test_audit_4_context_multi_path_pruning():
    """Verifies context adapter strictly enforces max_paths_per_chunk and orders paths by (-score, depth)."""
    from md_generator.adapters.langchain.context import PromptContextBuilder
    
    builder = PromptContextBuilder(max_tokens=4000)
    adapter = GraphContextAdapter(context_builder=builder, max_paths_per_chunk=3)
    
    paths = [
        GraphPath(seed_chunk_id="c1", target_node_id=f"target_{i}", node_ids=["c1", f"t_{i}"], edge_ids=[f"e_{i}"], depth=i % 3 + 1, score=round(0.1 * i, 2))
        for i in range(10)
    ]
    formatted = adapter.format_graph_paths(paths)
    lines = [line for line in formatted.split("\n") if line.strip()]
    assert len(lines) == 3
    
    assert "score 0.90" in lines[0]
    assert "score 0.80" in lines[1]
    assert "score 0.70" in lines[2]


def test_audit_5_serialization_empty_and_self_loops():
    """Verifies empty graphs, self-loops, and parallel multi-type edges serialize cleanly."""
    tenant = "t_empty"
    empty_kg = KnowledgeGraph(tenant_id=tenant, nodes={}, edges={})
    
    ld_empty = to_json_ld(empty_kg)
    assert ld_empty["@graph"]["nodes"] == []
    assert ld_empty["@graph"]["edges"] == []
    
    cy_empty = to_cytoscape(empty_kg)
    assert cy_empty["elements"]["nodes"] == []
    assert cy_empty["elements"]["edges"] == []
    
    stmts_empty = to_cypher_statements(empty_kg)
    assert stmts_empty == []
    
    n1 = EntityNode(node_id="n1", tenant_id=tenant, entity_id="e1", entity_type="class", name="A", qualified_name="p.A")
    n2 = EntityNode(node_id="n2", tenant_id=tenant, entity_id="e2", entity_type="class", name="B", qualified_name="p.B")
    
    e_self = RelationEdge(edge_id="e-self", tenant_id=tenant, source_id="n1", target_id="n1", relationship_type="SELF_CALL", weight=1.0)
    e_calls = RelationEdge(edge_id="e-calls", tenant_id=tenant, source_id="n1", target_id="n2", relationship_type="CALLS", weight=0.9)
    e_extends = RelationEdge(edge_id="e-extends", tenant_id=tenant, source_id="n1", target_id="n2", relationship_type="EXTENDS", weight=0.8)
    e_uses = RelationEdge(edge_id="e-uses", tenant_id=tenant, source_id="n1", target_id="n2", relationship_type="USES", weight=0.7)
    
    multi_kg = KnowledgeGraph(
        tenant_id=tenant,
        nodes={"n1": n1, "n2": n2},
        edges={"e-self": e_self, "e-calls": e_calls, "e-extends": e_extends, "e-uses": e_uses},
    )
    cy_multi = to_cytoscape(multi_kg)
    assert len(cy_multi["elements"]["edges"]) == 4
    edge_labels = {e["data"]["label"] for e in cy_multi["elements"]["edges"]}
    assert edge_labels == {"SELF_CALL", "CALLS", "EXTENDS", "USES"}
    
    stmts_multi = to_cypher_statements(multi_kg)
    assert len(stmts_multi) == 6
