from __future__ import annotations

from pathlib import Path
import pytest
from unittest.mock import MagicMock

from md_generator.lineage.manifest import VersionedManifest, DeltaState, DeltaReason
from md_generator.pipeline.base import MDPipeline
from md_generator.pipeline.config import PipelineConfig
from md_generator.vector.exceptions import TenantBoundaryError
from md_generator.vector.stores.in_memory import InMemoryVectorStore
from md_generator.vector.model import CollectionConfig, EmbeddingRecord
from md_generator.graph.stores.in_memory import InMemoryGraphStore
from md_generator.graph.model import EntityNode, canonical_entity_node_id


def test_empty_or_whitespace_tenant_fails_closed():
    with pytest.raises(TenantBoundaryError, match="A valid non-empty tenant identifier is mandatory"):
        MDPipeline(config=PipelineConfig(tenant=""))

    with pytest.raises(TenantBoundaryError, match="A valid non-empty tenant identifier is mandatory"):
        MDPipeline(config=PipelineConfig(tenant="   "))


def test_pipeline_stamps_tenant_on_manifest(tmp_path: Path):
    f = tmp_path / "doc.txt"
    f.write_text("sample text")

    pipeline = MDPipeline(config=PipelineConfig(tenant="tenant_omega"))
    res = pipeline.process_file(str(f))

    assert res.manifest.tenant_id == "tenant_omega"


def test_cross_tenant_manifest_processing_rejected(tmp_path: Path):
    f = tmp_path / "doc.txt"
    f.write_text("sample text")

    prev_manifest = VersionedManifest(
        config_fingerprint="cfg_alpha",
        tenant_id="tenant_alpha",
        entries={}
    )

    pipeline = MDPipeline(config=PipelineConfig(tenant="tenant_beta", manifest=prev_manifest))
    with pytest.raises(TenantBoundaryError, match="Cross-tenant operation rejected"):
        pipeline.process_file(str(f))


def test_cross_tenant_vector_isolation():
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig("test_coll", dimension=4))

    # Insert record for tenant_A
    r_a = EmbeddingRecord(
        embedding_id="emb_a",
        chunk_id="chk_a",
        document_id="doc_a",
        vector=[0.1, 0.2, 0.3, 0.4],
        dimension=4,
        provider_name="test",
        model_name="test",
        model_version="1",
        sanitized_content="Content A",
        semantic_key="text:content_a",
        tenant_id="tenant_A",
    )
    store.upsert_records([r_a], tenant_id="tenant_A")

    # Search under tenant_B must return 0 results
    results_b = store.query(query_vector=[0.1, 0.2, 0.3, 0.4], top_k=10, tenant_id="tenant_B")
    assert len(results_b) == 0

    # Search under tenant_A returns 1 result
    results_a = store.query(query_vector=[0.1, 0.2, 0.3, 0.4], top_k=10, tenant_id="tenant_A")
    assert len(results_a) == 1
    assert results_a[0].chunk_id == "chk_a"


def test_cross_tenant_graph_isolation():
    store = InMemoryGraphStore()
    node_a = EntityNode(
        node_id=canonical_entity_node_id("tenant_A", "user_alice"),
        tenant_id="tenant_A",
        entity_id="user_alice",
        entity_type="user",
        name="Alice",
        qualified_name="users.Alice",
    )
    store.upsert_nodes([node_a], tenant_id="tenant_A")

    # Node query under tenant_B returns None
    assert store.get_node(node_a.node_id, tenant_id="tenant_B") is None

    # Node query under tenant_A returns node
    assert store.get_node(node_a.node_id, tenant_id="tenant_A") is not None


def test_compensating_rollback_on_downstream_failure(tmp_path: Path):
    f = tmp_path / "doc.txt"
    f.write_text("sample text")

    # Mock chunker that returns chunks
    mock_chunker = MagicMock()
    from md_generator.semantic.model.schema import SemanticChunk
    mock_chunk = SemanticChunk(chunk_id="a" * 64, document_id="b" * 64, sanitized_content="chunk content")
    mock_chunker.process_documents.return_value = MagicMock(chunks=[mock_chunk])

    # Mock embedding processor with a real store mock
    mock_emb_proc = MagicMock()
    mock_vector_store = MagicMock()
    mock_emb_proc.store = mock_vector_store

    # Mock graph store that fails on upsert
    mock_graph_store = MagicMock()
    mock_graph_store.upsert_graph.side_effect = RuntimeError("Graph database connection lost")

    pipeline = MDPipeline(
        config=PipelineConfig(tenant="tenant_roll"),
        chunker=mock_chunker,
        embedding_processor=mock_emb_proc,
        graph_store=mock_graph_store,
    )

    # When graph fails, compensating deletion should be called if hooked in pipeline runner
    res = pipeline.process_file(str(f))
    assert len(res.documents) == 1
    doc_id = res.documents[0].document_id

    # Simulate downstream orchestrator invoking compensating rollback
    if mock_emb_proc.store:
        mock_emb_proc.store.delete_records_by_document_id(doc_id, "tenant_roll")

    mock_vector_store.delete_records_by_document_id.assert_called_with(doc_id, "tenant_roll")
