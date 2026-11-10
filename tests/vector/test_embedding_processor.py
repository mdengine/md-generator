"""Unit tests for EmbeddingProcessor, delta sync skipping, secret stripping, and tombstone purging."""

import os
import tempfile
import pytest

from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk
from md_generator.semantic.processor import SemanticProcessingResult
from md_generator.vector.exceptions import TenantBoundaryError
from md_generator.vector.model import (
    EmbeddingRecord,
    VectorSyncManifestStore,
    manifest_document_key,
    manifest_record_key,
)
from md_generator.vector.processor import (
    EmbeddingProcessor,
    sanitize_config_recursive,
    compute_embedding_processing_fingerprint,
    compute_embedding_id,
)
from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.stores.in_memory import InMemoryVectorStore


def test_sanitize_config_recursive():
    raw_config = {
        "endpoint": "https://api.openai.com",
        "api_key": "secret_123",
        "nested": {
            "Access_Token": "bearer_456",
            "model_params": {"temperature": 0.0, "password": "pass"},
        },
        "items": [{"TOKEN": "abc"}, {"name": "public"}],
    }

    cleaned = sanitize_config_recursive(raw_config)
    assert "api_key" not in cleaned
    assert "Access_Token" not in cleaned["nested"]
    assert "password" not in cleaned["nested"]["model_params"]
    assert "TOKEN" not in cleaned["items"][0]
    assert cleaned["endpoint"] == "https://api.openai.com"
    assert cleaned["nested"]["model_params"]["temperature"] == 0.0

    # Ensure original config was not mutated
    assert "api_key" in raw_config


def test_embedding_processor_end_to_end_and_delta_skip():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "sync_manifest.json")
        provider = MockEmbeddingProvider(dimension=64)
        store = InMemoryVectorStore()

        processor = EmbeddingProcessor(
            provider=provider,
            store=store,
            manifest_filepath=manifest_path,
            collection_name="test_col",
        )

        doc = SemanticDocument(
            document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            sanitized_content="def foo(): pass\ndef bar(): pass",
            document_type="code",
        )

        chunk1 = SemanticChunk(
            chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            document_id=doc.document_id,
            sanitized_content="def foo(): pass",
        )

        chunk2 = SemanticChunk(
            chunk_id="c2b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            document_id=doc.document_id,
            sanitized_content="def bar(): pass",
        )

        result_obj = SemanticProcessingResult(
            chunks=[chunk1, chunk2],
            semantic_processing_fingerprint="doc_fp_100",
        )

        # First sync run: should embed 2 chunks
        sync_res1 = processor.sync_semantic_result(result_obj, tenant_id="tenant_x")
        assert sync_res1.total_chunks == 2
        assert sync_res1.embedded_count == 2
        assert sync_res1.skipped_unchanged_count == 0

        # Query vector store to verify vectors were upserted
        query_res = store.query(query_vector=[0.1] * 64, top_k=5, tenant_id="tenant_x")
        assert len(query_res) == 2

        # Second sync run: exact same result -> 0 duplicate embeddings, 0 store calls, 2 skipped!
        sync_res2 = processor.sync_semantic_result(result_obj, tenant_id="tenant_x")
        assert sync_res2.total_chunks == 2
        assert sync_res2.embedded_count == 0
        assert sync_res2.skipped_unchanged_count == 2

        # Purge tombstones
        purged = processor.purge_document_tombstones(doc.document_id, tenant_id="tenant_x")
        assert purged == 2
        assert len(store.query(query_vector=[0.1] * 64, top_k=5, tenant_id="tenant_x")) == 0

        # Manifest loaded from disk should also have 0 records for doc
        reloaded_manifest = VectorSyncManifestStore.load(manifest_path)
        doc_key = manifest_document_key("tenant_x", doc.document_id)
        assert doc_key not in reloaded_manifest.document_to_chunks


def test_embedding_processor_tenant_mandatory():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "sync_manifest.json")
        provider = MockEmbeddingProvider()
        store = InMemoryVectorStore()
        processor = EmbeddingProcessor(provider=provider, store=store, manifest_filepath=manifest_path)

        with pytest.raises(TenantBoundaryError):
            processor.sync_semantic_result(SemanticProcessingResult(), tenant_id="")

        with pytest.raises(TenantBoundaryError):
            processor.sync_semantic_result(SemanticProcessingResult(), tenant_id=None)  # type: ignore
