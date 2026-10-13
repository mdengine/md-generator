from unittest.mock import MagicMock
import pytest

from md_generator.graph.hybrid.retriever import HybridGraphRAGRetriever
from md_generator.graph.model import EntityNode, RelationEdge, canonical_chunk_node_id
from md_generator.graph.stores.in_memory import InMemoryGraphStore


class DummyDoc:
    def __init__(self, chunk_id: str, score: float, tenant_id: str):
        self.page_content = f"content of {chunk_id}"
        self.metadata = {"chunk_id": chunk_id, "score": score, "tenant_id": tenant_id}


def test_deterministic_ranking_across_runs():
    tenant = "tenant-1"
    store = InMemoryGraphStore()

    # Create 5 chunks in a linear path
    nodes = []
    edges = []
    for i in range(1, 6):
        cid = f"c-{i}"
        nid = canonical_chunk_node_id(tenant, cid)
        nodes.append(EntityNode(node_id=nid, tenant_id=tenant, entity_id=cid, entity_type="chunk", name=cid, qualified_name=cid, chunk_ids=[cid]))

    for i in range(1, 5):
        edges.append(RelationEdge(
            edge_id=f"e-{i}-{i+1}",
            tenant_id=tenant,
            source_id=canonical_chunk_node_id(tenant, f"c-{i}"),
            target_id=canonical_chunk_node_id(tenant, f"c-{i+1}"),
            relationship_type="NEXT_CHUNK",
            weight=0.9,
        ))

    store.upsert_nodes(nodes, tenant_id=tenant)
    store.upsert_edges(edges, tenant_id=tenant)

    mock_vec = MagicMock()
    mock_vec.tenant_id = tenant
    mock_vec.invoke.return_value = [
        DummyDoc("c-1", 0.95, tenant),
        DummyDoc("c-2", 0.85, tenant),
    ]

    retriever1 = HybridGraphRAGRetriever(
        vector_retriever=mock_vec, graph_store=store, tenant_id=tenant, top_k=5, max_depth=2
    )
    retriever2 = HybridGraphRAGRetriever(
        vector_retriever=mock_vec, graph_store=store, tenant_id=tenant, top_k=5, max_depth=2
    )

    res1 = retriever1.retrieve("query")
    res2 = retriever2.retrieve("query")

    assert len(res1) == len(res2)
    for r1, r2 in zip(res1, res2):
        assert r1.chunk_id == r2.chunk_id
        assert r1.hybrid_score == r2.hybrid_score
        assert r1.vector_score == r2.vector_score
        assert r1.graph_score == r2.graph_score
        assert r1.provenance == r2.provenance


def test_equal_score_tie_breaking_order_independence():
    """Equal-score candidate documents supplied in reversed order produce identical ranking."""
    tenant = "tenant-1"
    store = InMemoryGraphStore()

    doc_a = DummyDoc("chunk_A", 0.85, tenant)
    doc_b = DummyDoc("chunk_B", 0.85, tenant)

    mock_vec_fwd = MagicMock()
    mock_vec_fwd.tenant_id = tenant
    mock_vec_fwd.invoke.return_value = [doc_a, doc_b]

    mock_vec_rev = MagicMock()
    mock_vec_rev.tenant_id = tenant
    mock_vec_rev.invoke.return_value = [doc_b, doc_a]

    retriever_fwd = HybridGraphRAGRetriever(
        vector_retriever=mock_vec_fwd, graph_store=store, tenant_id=tenant, top_k=5, max_depth=0
    )
    retriever_rev = HybridGraphRAGRetriever(
        vector_retriever=mock_vec_rev, graph_store=store, tenant_id=tenant, top_k=5, max_depth=0
    )

    res_fwd = retriever_fwd.retrieve("query")
    res_rev = retriever_rev.retrieve("query")

    order_fwd = [r.chunk_id for r in res_fwd]
    order_rev = [r.chunk_id for r in res_rev]
    assert order_fwd == order_rev == ["chunk_A", "chunk_B"]


def test_shuffled_candidates_determinism():
    """100 shuffled candidate configurations produce identical output order and scores."""
    import random
    tenant = "tenant-1"
    store = InMemoryGraphStore()

    docs = [
        DummyDoc(f"chunk_{i:03d}", round(0.5 + (i % 5) * 0.1, 2), tenant)
        for i in range(50)
    ]

    mock_vec = MagicMock()
    mock_vec.tenant_id = tenant
    mock_vec.invoke.return_value = list(docs)

    base_retriever = HybridGraphRAGRetriever(
        vector_retriever=mock_vec, graph_store=store, tenant_id=tenant, top_k=20, max_depth=0
    )
    base_result = [r.chunk_id for r in base_retriever.retrieve("query")]

    for seed in range(5):
        shuffled = list(docs)
        random.Random(seed).shuffle(shuffled)
        mock_vec.invoke.return_value = shuffled
        shuffled_retriever = HybridGraphRAGRetriever(
            vector_retriever=mock_vec, graph_store=store, tenant_id=tenant, top_k=20, max_depth=0
        )
        shuffled_result = [r.chunk_id for r in shuffled_retriever.retrieve("query")]
        assert shuffled_result == base_result
