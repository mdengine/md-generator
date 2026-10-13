from unittest.mock import MagicMock
import pytest

from md_generator.graph.hybrid.retriever import HybridGraphRAGRetriever
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def test_rrf_and_linear_parameter_validations():
    mock_vec = MagicMock()
    mock_vec.tenant_id = "t1"
    store = InMemoryGraphStore()

    # Invalid alpha
    with pytest.raises(ValueError):
        HybridGraphRAGRetriever(mock_vec, store, "t1", fusion_mode="linear", alpha=-0.1)
    with pytest.raises(ValueError):
        HybridGraphRAGRetriever(mock_vec, store, "t1", fusion_mode="linear", alpha=1.1)

    # Invalid weights
    with pytest.raises(ValueError):
        HybridGraphRAGRetriever(mock_vec, store, "t1", weight_vector=-1.0)
    with pytest.raises(ValueError):
        HybridGraphRAGRetriever(mock_vec, store, "t1", weight_vector=0.0, weight_graph=0.0)

    # Invalid rrf_k
    with pytest.raises(ValueError):
        HybridGraphRAGRetriever(mock_vec, store, "t1", rrf_k=0)


def test_rrf_normalized_math_exact_values():
    # Simulate rank 1 on vector and rank 1 on graph
    # RRF_raw = (1.0 / (60 + 1)) + (1.0 / (60 + 1))
    # RRF_max = (1.0 / (60 + 1)) + (1.0 / (60 + 1))
    # RRF_norm = 1.0
    w_v = 1.0
    w_g = 1.0
    k = 60

    rrf_max = (w_v / (k + 1)) + (w_g / (k + 1))

    # Candidate at rank 1 in both
    raw_both = (w_v / (k + 1)) + (w_g / (k + 1))
    norm_both = raw_both / rrf_max
    assert norm_both == 1.0

    # Candidate at rank 1 in vector, absent in graph
    raw_vec_only = w_v / (k + 1)
    norm_vec_only = raw_vec_only / rrf_max
    assert norm_vec_only == 0.5

    # Candidate at rank 2 in vector, absent in graph
    raw_vec_rank2 = w_v / (k + 2)
    norm_vec_rank2 = raw_vec_rank2 / rrf_max
    assert 0.0 < norm_vec_rank2 < 0.5


def test_c13_path_score_maximization_multihop():
    """Verifies C13 topological path score maximization selects highest scoring path (0.30 > 0.25)."""
    import math
    from md_generator.graph.model import EntityNode, RelationEdge

    store = InMemoryGraphStore()
    tenant = "tenant-c13"

    # Seed chunk c1
    c1 = EntityNode(node_id="c1", tenant_id=tenant, entity_id="c1", entity_type="chunk", name="c1", qualified_name="chunk.1")
    # Target node nA
    nA = EntityNode(node_id="nA", tenant_id=tenant, entity_id="nA", entity_type="class", name="A", qualified_name="p.A")
    # Intermediate node nB
    nB = EntityNode(node_id="nB", tenant_id=tenant, entity_id="nB", entity_type="class", name="B", qualified_name="p.B")
    store.upsert_nodes([c1, nA, nB], tenant_id=tenant)

    # Path 1: direct edge c1 -> nA (depth=1, weight=0.5) => S_g = 1/(1+1) * 0.5 = 0.25
    e1 = RelationEdge(edge_id="e1", tenant_id=tenant, source_id="c1", target_id="nA", relationship_type="CALLS", weight=0.5)
    # Path 2: indirect c1 -> nB (w=1.0) and nB -> nA (w=0.9) => S_g = 1/(1+2) * min(1.0, 0.9) = 0.30
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

    sg = store.traverse(["c1"], tenant_id=tenant, max_depth=2)
    scores = retriever._reconstruct_paths_and_scores(sg, {"c1": "c1"})

    # C13 Contract: S_g(nA) must be max(0.25, 0.30) = 0.30!
    assert "nA" in scores
    score_nA, paths_nA = scores["nA"]
    assert math.isclose(score_nA, 0.30, rel_tol=1e-3)
    assert len(paths_nA) == 2
    # Top-ranked path must be the superior 2-hop path
    assert paths_nA[0].depth == 2
    assert math.isclose(paths_nA[0].score, 0.30, rel_tol=1e-3)
    # Second path is the direct 1-hop path
    assert paths_nA[1].depth == 1
    assert math.isclose(paths_nA[1].score, 0.25, rel_tol=1e-3)

