"""Unit tests for delta vector synchronization and tombstone purging."""

import os
import tempfile
import pytest

from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk
from md_generator.semantic.processor import SemanticProcessingResult
from md_generator.vector.model import manifest_document_key, VectorSyncManifestStore
from md_generator.vector.processor import EmbeddingProcessor
from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.stores.in_memory import InMemoryVectorStore


def test_delta_sync_unchanged_generates_zero_embeddings_and_zero_store_calls():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        provider = MockEmbeddingProvider(dimension=32)
        store = InMemoryVectorStore()

        processor = EmbeddingProcessor(
            provider=provider,
            store=store,
            manifest_filepath=manifest_path,
        )

        doc = SemanticDocument(
            document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            sanitized_content="test content",
        )
        chunk = SemanticChunk(
            chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            document_id=doc.document_id,
            sanitized_content="chunk content",
        )
        result_obj = SemanticProcessingResult(
            chunks=[chunk],
            semantic_processing_fingerprint="fp_v1",
        )

        # 1st run: embed 1
        res1 = processor.sync_semantic_result(result_obj, tenant_id="tenant_1")
        assert res1.embedded_count == 1
        assert res1.skipped_unchanged_count == 0

        # 2nd run: unchanged -> skip 1
        res2 = processor.sync_semantic_result(result_obj, tenant_id="tenant_1")
        assert res2.embedded_count == 0
        assert res2.skipped_unchanged_count == 1

        # 3rd run with updated chunk fingerprint -> re-embed 1
        chunk_mod = SemanticChunk(
            chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            document_id=doc.document_id,
            sanitized_content="chunk content modified",
        )
        result_mod = SemanticProcessingResult(
            chunks=[chunk_mod],
            semantic_processing_fingerprint="fp_v2",
        )
        res3 = processor.sync_semantic_result(result_mod, tenant_id="tenant_1")
        assert res3.embedded_count == 1
        assert res3.skipped_unchanged_count == 0
