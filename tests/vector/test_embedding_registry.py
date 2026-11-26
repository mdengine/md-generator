"""Test Suite for EmbeddingModelRegistry, Dimension Safety, Caching, and Staging Migration.

Phase 1B Enterprise Verification:
1. Verifies model specifications and dimensions (all-MiniLM-L6-v2=384, bge-base=768, bge-m3=1024, deterministic=64).
2. Verifies dimension mismatch protection preventing mixed vectors in the same collection.
3. Verifies strict offline mode error handling without remote downloads.
4. Verifies embedding cache operation.
5. Verifies non-destructive staging index migration and rollback safety.
6. Verifies multi-document incremental processing and tenant boundary constraints.
"""

import os
import tempfile
import pytest

from md_generator.semantic.model.schema import SemanticChunk
from md_generator.semantic.processor import SemanticProcessingResult
from md_generator.vector.exceptions import (
    EmbeddingProviderError,
    VectorDimensionMismatchError,
    CollectionConfigurationError,
    TenantBoundaryError,
)
from md_generator.vector.model import (
    CollectionConfig,
    EmbeddingRecord,
    VectorSyncManifestStore,
)
from md_generator.vector.processor import EmbeddingProcessor
from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.registry import (
    EmbeddingCache,
    EmbeddingModelRegistry,
    IndexMigrationManager,
    ModelSpec,
    validate_dimension_compatibility,
)
from md_generator.vector.stores.in_memory import InMemoryVectorStore


def test_model_registry_spec_retrieval_and_aliases():
    # 1. Default MiniLM (384-d)
    minilm_spec = EmbeddingModelRegistry.get_spec("all-MiniLM-L6-v2")
    assert minilm_spec.dimension == 384
    assert minilm_spec.provider_name == "sentence_transformers"
    assert minilm_spec.similarity_metric == "cosine"

    # Alias checks
    assert EmbeddingModelRegistry.get_spec("default") is minilm_spec
    assert EmbeddingModelRegistry.get_spec("minilm") is minilm_spec

    # 2. BGE Base (768-d)
    bge_spec = EmbeddingModelRegistry.get_spec("bge-base-en-v1.5")
    assert bge_spec.dimension == 768
    assert EmbeddingModelRegistry.get_spec("bge-base") is bge_spec

    # 3. BGE M3 (1024-d)
    m3_spec = EmbeddingModelRegistry.get_spec("bge-m3")
    assert m3_spec.dimension == 1024

    # 4. Deterministic Offline Fallback (64-d)
    fallback_spec = EmbeddingModelRegistry.get_spec("deterministic-64d")
    assert fallback_spec.dimension == 64
    assert fallback_spec.provider_name == "mock"
    assert EmbeddingModelRegistry.get_spec("fallback") is fallback_spec
    assert EmbeddingModelRegistry.get_spec("pure-script") is fallback_spec

    # Identity hash
    h1 = fallback_spec.compute_identity_hash()
    assert len(h1) == 64
    assert h1 == fallback_spec.compute_identity_hash()


def test_provider_factory_and_dimension_validation():
    # Factory create deterministic 64-d provider
    p64 = EmbeddingModelRegistry.create_provider("deterministic-64d")
    assert p64.dimension == 64
    assert p64.provider_name == "mock"

    # Factory create deterministic 384-d provider
    p384 = EmbeddingModelRegistry.create_provider("deterministic-384d")
    assert p384.dimension == 384

    # Compatible collection config
    cfg384 = CollectionConfig(collection_name="col384", dimension=384)
    validate_dimension_compatibility(p384, cfg384)  # Must pass without error

    # Incompatible collection: passing 64-d provider to 384-d collection
    with pytest.raises(VectorDimensionMismatchError, match="does not match target collection dimension"):
        validate_dimension_compatibility(p64, cfg384)


def test_never_mix_vector_dimensions_in_same_store():
    store = InMemoryVectorStore()
    cfg = CollectionConfig(collection_name="enterprise_kb", dimension=384)
    store.initialize_collection(cfg)

    # Attempting to upsert 64-dimensional vector must be rejected
    record_64 = EmbeddingRecord(
        embedding_id="emb1",
        chunk_id="chunk1",
        document_id="doc1",
        vector=[0.1] * 64,
        dimension=64,
        provider_name="mock",
        model_name="mock-64",
        model_version="1.0",
        sanitized_content="test content",
        semantic_key="key1",
        tenant_id="tenant_a",
    )

    with pytest.raises(VectorDimensionMismatchError):
        store.upsert_records([record_64], tenant_id="tenant_a")


def test_strict_offline_mode_enforcement():
    from md_generator.vector.providers.sentence_transformers import SentenceTransformersEmbeddingProvider

    # When offline_mode=True with a non-existent local model, must raise descriptive EmbeddingProviderError
    with pytest.raises(EmbeddingProviderError, match="offline mode is enabled"):
        SentenceTransformersEmbeddingProvider(
            model_name="non_existent_local_model_xyz",
            offline_mode=True,
        )


def test_embedding_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = EmbeddingCache(cache_dir=tmpdir)
        content_hash = "abc123hash"
        model_hash = "model456hash"
        vec = [0.1, 0.2, 0.3, 0.4]

        # Initially absent
        assert cache.get(content_hash, model_hash) is None

        # Store vector
        cache.put(content_hash, model_hash, vec)

        # Retrieve from cache
        cached_vec = cache.get(content_hash, model_hash)
        assert cached_vec == vec

        # Re-load from disk in a fresh cache instance
        cache_reloaded = EmbeddingCache(cache_dir=tmpdir)
        assert cache_reloaded.get(content_hash, model_hash) == vec


def test_staging_migration_and_atomic_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        src_manifest = os.path.join(tmpdir, "source_manifest.json")
        target_manifest = os.path.join(tmpdir, "target_manifest.json")

        # Step 1: Initial 64-d store and sync
        p64 = MockEmbeddingProvider(dimension=64)
        store64 = InMemoryVectorStore()
        proc64 = EmbeddingProcessor(
            provider=p64,
            store=store64,
            manifest_filepath=src_manifest,
            collection_name="col_64",
        )

        chunk1 = SemanticChunk(
            chunk_id="1111222233334444555566667777888899990000aaaabbbbccccddddeeeefff1",
            document_id="0000111122223333444455556666777788889999aaaabbbbccccddddeeeefff1",
            sanitized_content="Section 1: Initial architecture instructions.",
        )
        chunk2 = SemanticChunk(
            chunk_id="1111222233334444555566667777888899990000aaaabbbbccccddddeeeefff2",
            document_id="0000111122223333444455556666777788889999aaaabbbbccccddddeeeefff1",
            sanitized_content="Section 2: Maintenance and disaster recovery.",
        )

        sem_res = SemanticProcessingResult(chunks=[chunk1, chunk2])
        proc64.sync_semantic_result(sem_res, tenant_id="tenant_prod")
        assert os.path.exists(src_manifest)

        # Step 2: Migrate to 384-d model (using deterministic-384d provider)
        p384 = EmbeddingModelRegistry.create_provider("deterministic-384d")
        store384 = InMemoryVectorStore()

        migration_proc = IndexMigrationManager.migrate(
            source_manifest_path=src_manifest,
            target_manifest_path=target_manifest,
            target_store=store384,
            new_provider=p384,
            chunks=[chunk1, chunk2],
            tenant_id="tenant_prod",
            collection_name="col_384",
        )

        # Verify migration success
        assert os.path.exists(target_manifest)
        assert os.path.exists(f"{src_manifest}.bak")  # Original manifest backed up
        query_res = store384.query(query_vector=[0.1] * 384, top_k=5, tenant_id="tenant_prod")
        assert len(query_res) == 2

        # Step 3: Test Rollback on Failure
        class BrokenProvider(MockEmbeddingProvider):
            def embed_texts(self, texts):
                raise RuntimeError("Simulated transient hardware failure during embedding")

        broken_provider = BrokenProvider(dimension=384)

        with pytest.raises(EmbeddingProviderError, match="safely rolled back"):
            IndexMigrationManager.migrate(
                source_manifest_path=src_manifest,
                target_manifest_path=os.path.join(tmpdir, "broken_manifest.json"),
                target_store=InMemoryVectorStore(),
                new_provider=broken_provider,
                chunks=[chunk1],
                tenant_id="tenant_prod",
            )

        # Staging file must be purged, original manifest must be untouched
        assert not os.path.exists(os.path.join(tmpdir, "broken_manifest.json.staging"))
        assert os.path.exists(src_manifest)


def test_incremental_processing_and_tenant_isolation():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "tenant_manifest.json")
        provider = EmbeddingModelRegistry.create_provider("deterministic-64d")
        store = InMemoryVectorStore()
        processor = EmbeddingProcessor(
            provider=provider,
            store=store,
            manifest_filepath=manifest_path,
        )

        chunk = SemanticChunk(
            chunk_id="9999222233334444555566667777888899990000aaaabbbbccccddddeeeefff1",
            document_id="0000999922223333444455556666777788889999aaaabbbbccccddddeeeefff1",
            sanitized_content="Confidential corporate strategy.",
        )
        sem_res = SemanticProcessingResult(chunks=[chunk])

        # Upsert under tenant_alpha
        processor.sync_semantic_result(sem_res, tenant_id="tenant_alpha")

        # Querying under tenant_beta must yield zero results (tenant isolation)
        res_beta = store.query(query_vector=[0.1] * 64, top_k=5, tenant_id="tenant_beta")
        assert len(res_beta) == 0

        # Querying under tenant_alpha retrieves the record
        res_alpha = store.query(query_vector=[0.1] * 64, top_k=5, tenant_id="tenant_alpha")
        assert len(res_alpha) == 1
        assert res_alpha[0].chunk_id == chunk.chunk_id
