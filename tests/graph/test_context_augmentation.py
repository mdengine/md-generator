import pytest

from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.graph.hybrid.context import GraphContextAdapter
from md_generator.graph.hybrid.retriever import ScoredHybridResult
from md_generator.graph.model import GraphPath, KnowledgeGraph, EntityNode


def test_graph_context_adapter_formatting():
    path = GraphPath(
        seed_chunk_id="chunk-1",
        target_node_id="target-node",
        node_ids=["chunk:1", "func:A", "table:B"],
        edge_ids=["e1", "e2"],
        depth=2,
        score=0.33,
    )

    kg = KnowledgeGraph(
        tenant_id="t1",
        nodes={
            "chunk:1": EntityNode(node_id="chunk:1", tenant_id="t1", entity_id="c1", entity_type="chunk", name="Chunk1", qualified_name="chunk.1"),
            "func:A": EntityNode(node_id="func:A", tenant_id="t1", entity_id="fA", entity_type="function", name="ProcessOrder", qualified_name="order.ProcessOrder"),
            "table:B": EntityNode(node_id="table:B", tenant_id="t1", entity_id="tB", entity_type="table", name="OrdersTable", qualified_name="db.OrdersTable"),
        },
    )

    adapter = GraphContextAdapter()
    formatted = adapter.format_graph_paths([path], subgraph=kg)

    assert "[Graph Path (depth 2, score 0.33):" in formatted
    assert "Chunk1 (chunk) -> ProcessOrder (function) -> OrdersTable (table)" in formatted


def test_graph_context_adapter_token_budget():
    builder = PromptContextBuilder(max_tokens=100, include_citations=True)
    adapter = GraphContextAdapter(context_builder=builder)

    res1 = ScoredHybridResult(
        chunk_id="c1",
        content="This is the primary text chunk for testing.",
        tenant_id="t1",
        vector_score=0.9,
        graph_score=0.8,
        hybrid_score=0.85,
        provenance="HYBRID",
        metadata={"document_id": "doc1", "chunk_id": "c1"},
    )
    # Very long result that would exceed remaining budget
    res2 = ScoredHybridResult(
        chunk_id="c2",
        content="Long text " * 200,
        tenant_id="t1",
        vector_score=0.5,
        graph_score=0.4,
        hybrid_score=0.45,
        provenance="VECTOR_ONLY",
        metadata={"document_id": "doc2", "chunk_id": "c2"},
    )

    prompt_context = adapter.build_context([res1, res2])
    assert "This is the primary text chunk for testing." in prompt_context
    assert "c1" in prompt_context
    # res2 was omitted due to token budget cap
    assert "Long text" not in prompt_context
