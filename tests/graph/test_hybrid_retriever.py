from unittest.mock import MagicMock
import pytest

from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.graph.hybrid.retriever import HybridGraphRAGRetriever, ScoredHybridResult
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    canonical_chunk_node_id,
    canonical_entity_node_id,
)
from md_generator.graph.stores.in_memory import InMemoryGraphStore


class DummyDoc:
    def __init__(self, content: str, chunk_id: str, score: float, tenant_id: str):
        self.page_content = content
        self.metadata = {
            "chunk_id": chunk_id,
            "score": score,
            "tenant_id": tenant_id,
        }


def test_hybrid_retriever_lifecycle_and_bridge():
    tenant = "tenant-1"
    store = InMemoryGraphStore()

    # Seed chunk node in graph
    c1_id = "chunk-1"
    c1_node_id = canonical_chunk_node_id(tenant, c1_id)
    c1_node = EntityNode(
        node_id=c1_node_id,
        tenant_id=tenant,
        entity_id=c1_id,
        entity_type="chunk",
        name="c1",
        qualified_name="chunk.1",
        chunk_ids=[c1_id],
    )

    # Connected entity node
    e1_node_id = canonical_entity_node_id(tenant, "ent-1")
    e1_node = EntityNode(
        node_id=e1_node_id,
        tenant_id=tenant,
        entity_id="ent-1",
        entity_type="function",
        name="process",
        qualified_name="pkg.process",
        chunk_ids=[c1_id],
    )

    edge = RelationEdge(
        edge_id="e-c1-e1",
        tenant_id=tenant,
        source_id=c1_node_id,
        target_id=e1_node_id,
        relationship_type="CONTAINS_ENTITY",
        weight=0.9,
    )
    store.upsert_nodes([c1_node, e1_node], tenant_id=tenant)
    store.upsert_edges([edge], tenant_id=tenant)

    # Mock vector retriever
    mock_vec = MagicMock()
    mock_vec.tenant_id = tenant
    mock_vec.invoke.return_value = [
        DummyDoc("vector chunk 1", c1_id, 0.85, tenant)
    ]

    retriever = HybridGraphRAGRetriever(
        vector_retriever=mock_vec,
        graph_store=store,
        tenant_id=tenant,
        top_k=5,
        max_depth=2,
        fusion_mode="rrf",
    )

    results = retriever.retrieve("query text")
    assert len(results) > 0
    top = results[0]
    assert top.chunk_id == c1_id
    assert 0.0 <= top.hybrid_score <= 1.0
    assert 0.0 <= top.vector_score <= 1.0
    assert 0.0 <= top.graph_score <= 1.0

    # Invoke returning LangChain Documents
    docs = retriever.invoke("query text")
    assert len(docs) > 0
    assert docs[0].metadata["tenant_id"] == tenant


def test_hybrid_retriever_tenant_mismatch():
    mock_vec = MagicMock()
    mock_vec.tenant_id = "tenant-other"

    store = InMemoryGraphStore()
    with pytest.raises(TenantBoundaryError):
        HybridGraphRAGRetriever(
            vector_retriever=mock_vec,
            graph_store=store,
            tenant_id="tenant-expected",
        )
