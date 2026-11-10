"""Unit tests for vector domain models, validation, composite keying, and atomic manifest store."""

import os
import math
import tempfile
import pytest

from md_generator.vector.exceptions import (
    VectorValueError,
    VectorDimensionMismatchError,
    CollectionConfigurationError,
)
from md_generator.vector.model import (
    EmbeddingRecord,
    VectorQueryResult,
    CollectionConfig,
    VectorSyncRecord,
    VectorSyncManifest,
    VectorSyncManifestStore,
    validate_vector,
    manifest_document_key,
    manifest_record_key,
)


def test_validate_vector_valid():
    validate_vector([0.1, 0.2, 0.3], expected_dimension=3)


def test_validate_vector_empty():
    with pytest.raises(VectorValueError, match="non-empty list"):
        validate_vector([])


def test_validate_vector_boolean_rejected():
    with pytest.raises(VectorValueError, match="invalid non-numeric"):
        validate_vector([True, 0.5])


def test_validate_vector_nan_rejected():
    with pytest.raises(VectorValueError, match="invalid non-numeric"):
        validate_vector([0.1, float("nan")])


def test_validate_vector_inf_rejected():
    with pytest.raises(VectorValueError, match="invalid non-numeric"):
        validate_vector([0.1, float("inf")])


def test_validate_vector_zero_magnitude():
    with pytest.raises(VectorValueError, match="zero"):
        validate_vector([0.0, 0.0, 0.0])


def test_validate_vector_dimension_mismatch():
    with pytest.raises(VectorDimensionMismatchError, match="does not match collection dimension"):
        validate_vector([0.1, 0.2], expected_dimension=3)


def test_embedding_record_post_init_validation():
    record = EmbeddingRecord(
        embedding_id="emb_1",
        chunk_id="chunk_1",
        document_id="doc_1",
        vector=[0.1, 0.2, 0.3],
        dimension=3,
        provider_name="mock",
        model_name="mock-model",
        model_version="1.0",
        sanitized_content="hello",
        semantic_key="key_1",
        tenant_id="tenant_a",
    )
    assert record.embedding_id == "emb_1"

    with pytest.raises(VectorValueError):
        EmbeddingRecord(
            embedding_id="emb_2",
            chunk_id="chunk_2",
            document_id="doc_2",
            vector=[float("nan"), 0.2],
            dimension=2,
            provider_name="mock",
            model_name="mock-model",
            model_version="1.0",
            sanitized_content="bad",
            semantic_key="key_2",
            tenant_id="tenant_a",
        )


def test_collection_config_validation():
    config = CollectionConfig(collection_name="test_col", dimension=128, distance_metric="cosine")
    assert config.collection_name == "test_col"
    assert config.dimension == 128

    with pytest.raises(CollectionConfigurationError, match="collection_name"):
        CollectionConfig(collection_name="")

    with pytest.raises(CollectionConfigurationError, match="dimension"):
        CollectionConfig(dimension=-5)

    with pytest.raises(CollectionConfigurationError, match="distance_metric"):
        CollectionConfig(distance_metric="invalid_metric")


def test_manifest_composite_keying_delimiter_safety():
    key1 = manifest_document_key("tenant:A", "doc:X")
    key2 = manifest_document_key("tenant:A:B", "doc:X")
    assert key1 != key2
    assert "tenant%3AA" in key1
    assert "tenant%3AA%3AB" in key2

    rec_key1 = manifest_record_key("tenant:1", "coll:A", "emb:X")
    rec_key2 = manifest_record_key("tenant:1", "coll:A:B", "emb:X")
    assert rec_key1 != rec_key2


def test_manifest_store_atomic_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "vector_manifest.json")
        manifest = VectorSyncManifest()
        
        doc_key = manifest_document_key("tenant_a", "doc_1")
        manifest.document_to_chunks[doc_key] = ["chunk_1", "chunk_2"]
        
        rec_key = manifest_record_key("tenant_a", "enterprise", "emb_1")
        record = VectorSyncRecord(
            tenant_id="tenant_a",
            document_id="doc_1",
            revision_id="rev_1",
            document_semantic_processing_fingerprint="doc_fp_1",
            chunk_id="chunk_1",
            chunk_semantic_processing_fingerprint="chunk_fp_1",
            provider_name="mock",
            model_name="mock-model",
            model_version="1.0",
            embedding_processing_fingerprint="emb_fp_1",
            embedding_id="emb_1",
            collection_name="enterprise",
            created_timestamp=1000.0,
        )
        manifest.records[rec_key] = record

        VectorSyncManifestStore.save_atomic(manifest, filepath)
        assert os.path.exists(filepath)

        loaded = VectorSyncManifestStore.load(filepath)
        assert loaded.version == "1.0"
        assert doc_key in loaded.document_to_chunks
        assert loaded.document_to_chunks[doc_key] == ["chunk_1", "chunk_2"]
        assert rec_key in loaded.records
        assert loaded.records[rec_key].embedding_id == "emb_1"
        assert loaded.records[rec_key].document_semantic_processing_fingerprint == "doc_fp_1"
