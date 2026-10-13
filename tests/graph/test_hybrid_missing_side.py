from unittest.mock import MagicMock
import pytest

from md_generator.graph.hybrid.retriever import HybridGraphRAGRetriever
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    canonical_chunk_node_id,
)
from md_generator.graph.stores.in_memory import InMemoryGraphStore


class DummyDoc:
    def __init__(self, chunk_id: str, score: float, tenant_id: str):
        self.page_content = f"content of {chunk_id}"
        self.metadata = {"chunk_id": chunk_id, "score": score, "tenant_id": tenant_id}


def test_candidate_set_membership_provenance_three_cases():
    tenant = "tenant-1"
    store = InMemoryGraphStore()

    # In graph: c_seed and c_graph_only
    c_seed_node_id = canonical_chunk_node_id(tenant, "c_seed")
    c_graph_node_id = canonical_chunk_node_id(tenant, "c_graph_only")

    node_seed = EntityNode(
        node_id=c_seed_node_id, tenant_id=tenant, entity_id="c_seed", entity_type="chunk", name="s", qualified_name="s", chunk_ids=["c_seed"]
    )
    node_graph = EntityNode(
        node_id=c_graph_node_id, tenant_id=tenant, entity_id="c_graph_only", entity_type="chunk", name="g", qualified_name="g", chunk_ids=["c_graph_only"]
    )
    edge = RelationEdge(
        edge_id="e-sg", tenant_id=tenant, source_id=c_seed_node_id, target_id=c_graph_node_id, relationship_type="CONNECTED_TO"
    )
    store.upsert_nodes([node_seed, node_graph], tenant_id=tenant)
    store.upsert_edges([edge], tenant_id=tenant)

    # Vector returns: c_seed (also in graph) AND c_vector_only (NOT in graph)
    mock_vec = MagicMock()
    mock_vec.tenant_id = tenant
    mock_vec.invoke.return_value = [
        DummyDoc("c_seed", 0.9, tenant),
        DummyDoc("c_vector_only", 0.8, tenant),
    ]

    retriever = HybridGraphRAGRetriever(
        vector_retriever=mock_vec,
        graph_store=store,
        tenant_id=tenant,
        top_k=10,
        max_depth=1,
        fusion_mode="rrf",
    )

    results = retriever.retrieve("query")
    res_map = {r.chunk_id: r for r in results}

    # Verify all 3 cases
    assert "c_seed" in res_map
    assert res_map["c_seed"].provenance == "HYBRID"

    assert "c_vector_only" in res_map
    assert res_map["c_vector_only"].provenance == "VECTOR_ONLY"
    assert res_map["c_vector_only"].graph_score == 0.0

    assert "c_graph_only" in res_map
    assert res_map["c_graph_only"].provenance == "GRAPH_ONLY"
    assert res_map["c_graph_only"].vector_score == 0.0
