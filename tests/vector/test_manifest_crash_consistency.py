"""Unit tests for atomic manifest store and partial batch upsert failure reconciliation state machine."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock

from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk
from md_generator.semantic.processor import SemanticProcessingResult
from md_generator.vector.model import (
    VectorSyncManifest,
    VectorSyncRecord,
    VectorSyncManifestStore,
    manifest_record_key,
)
from md_generator.vector.processor import EmbeddingProcessor
from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.stores.in_memory import InMemoryVectorStore


def test_manifest_store_partial_failure_reconciliation():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        provider = MockEmbeddingProvider(dimension=16)
        store = InMemoryVectorStore()

        processor = EmbeddingProcessor(
            provider=provider,
            store=store,
            manifest_filepath=manifest_path,
        )

        doc = SemanticDocument(
            document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            sanitized_content="content",
        )
        chunk = SemanticChunk(
            chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            document_id=doc.document_id,
            sanitized_content="chunk",
        )
        result_obj = SemanticProcessingResult(
            chunks=[chunk],
            semantic_processing_fingerprint="fp1",
        )

        # Mock store upsert failure (raises exception or returns N < len(records))
        faulty_store = InMemoryVectorStore()
        faulty_store.initialize_collection(processor.store.config)  # type: ignore
        faulty_store.upsert_records = MagicMock(side_effect=RuntimeError("Store connection dropped"))

        processor_faulty = EmbeddingProcessor(
            provider=provider,
            store=faulty_store,
            manifest_filepath=manifest_path,
        )

        # Sync with faulty store: raises/fails -> ZERO manifest commits
        res = processor_faulty.sync_semantic_result(result_obj, tenant_id="tenant_1")
        assert res.failed_count == 1
        assert res.embedded_count == 0

        # Verify manifest file on disk has 0 records
        loaded_manifest = VectorSyncManifestStore.load(manifest_path)
        assert len(loaded_manifest.records) == 0

        # Now test reconciliation API
        rec_key = manifest_record_key("tenant_1", "enterprise_knowledge", "emb_100")
        candidate_rec = VectorSyncRecord(
            tenant_id="tenant_1",
            document_id=doc.document_id,
            revision_id="v1",
            document_semantic_processing_fingerprint="fp1",
            chunk_id=chunk.chunk_id,
            chunk_semantic_processing_fingerprint="fp1",
            provider_name="mock",
            model_name="m1",
            model_version="1.0",
            embedding_processing_fingerprint="emb_fp",
            embedding_id="emb_100",
            collection_name="enterprise_knowledge",
            created_timestamp=100.0,
        )

        # Manually upsert record to store to simulate background recovery
        from md_generator.vector.model import EmbeddingRecord
        rec = EmbeddingRecord(
            embedding_id="emb_100",
            chunk_id=chunk.chunk_id,
            document_id=doc.document_id,
            vector=[0.1] * 16,
            dimension=16,
            provider_name="mock",
            model_name="m1",
            model_version="1.0",
            sanitized_content="chunk",
            semantic_key="k1",
            tenant_id="tenant_1",
        )
        store.upsert_records([rec], tenant_id="tenant_1")

        # Reconcile unconfirmed vectors
        reconciled = processor.reconcile_unconfirmed_vectors("tenant_1", [(rec_key, candidate_rec)])
        assert reconciled == 1

        # Verify manifest now contains the confirmed record
        reloaded_manifest = VectorSyncManifestStore.load(manifest_path)
        assert rec_key in reloaded_manifest.records
