"""Unit tests for InMemoryVectorStore and metric scoring."""

import pytest
from md_generator.vector.exceptions import (
    CollectionConfigurationError,
    TenantBoundaryError,
)
from md_generator.vector.model import CollectionConfig, EmbeddingRecord
from md_generator.vector.stores import InMemoryVectorStore, StoreRegistry


def test_in_memory_store_initialization_immutability():
    store = InMemoryVectorStore()
    config1 = CollectionConfig(collection_name="col1", dimension=3, distance_metric="cosine")
    store.initialize_collection(config1)

    # Identical call is no-op
    store.initialize_collection(config1)

    # Conflicting call raises CollectionConfigurationError
    config2 = CollectionConfig(collection_name="col2", dimension=3, distance_metric="cosine")
    with pytest.raises(CollectionConfigurationError, match="conflicting collection parameters"):
        store.initialize_collection(config2)


def test_in_memory_store_uninitialized_raises():
    store = InMemoryVectorStore()
    with pytest.raises(CollectionConfigurationError, match="not initialized"):
        store.upsert_records([], tenant_id="tenant_a")


def test_in_memory_store_tenant_boundary():
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(dimension=2))

    record_a = EmbeddingRecord(
        embedding_id="e1",
        chunk_id="c1",
        document_id="d1",
        vector=[1.0, 0.0],
        dimension=2,
        provider_name="mock",
        model_name="m1",
        model_version="1.0",
        sanitized_content="a",
        semantic_key="k1",
        tenant_id="tenant_a",
    )

    # Cross-tenant record upsert raises TenantBoundaryError
    with pytest.raises(TenantBoundaryError, match="does not match operation tenant_id"):
        store.upsert_records([record_a], tenant_id="tenant_b")

    # Invalid tenant_id raises TenantBoundaryError
    with pytest.raises(TenantBoundaryError):
        store.upsert_records([record_a], tenant_id="")

    with pytest.raises(TenantBoundaryError):
        store.upsert_records([record_a], tenant_id=None)  # type: ignore


def test_in_memory_store_upsert_query_delete():
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(collection_name="enterprise", dimension=2, distance_metric="cosine"))

    rec1 = EmbeddingRecord(
        embedding_id="e1",
        chunk_id="c1",
        document_id="doc1",
        vector=[1.0, 0.0],
        dimension=2,
        provider_name="mock",
        model_name="m1",
        model_version="1.0",
        sanitized_content="doc1 content",
        semantic_key="k1",
        tenant_id="tenant_a",
    )
    rec2 = EmbeddingRecord(
        embedding_id="e2",
        chunk_id="c2",
        document_id="doc1",
        vector=[0.0, 1.0],
        dimension=2,
        provider_name="mock",
        model_name="m1",
        model_version="1.0",
        sanitized_content="doc1 chunk 2",
        semantic_key="k2",
        tenant_id="tenant_a",
    )

    assert store.upsert_records([rec1, rec2], tenant_id="tenant_a") == 2

    # Query with tenant_a
    results = store.query(query_vector=[1.0, 0.0], top_k=2, tenant_id="tenant_a")
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].score == pytest.approx(1.0)
    assert results[1].chunk_id == "c2"
    assert results[1].score == pytest.approx(0.0)

    # Cross-tenant query returns 0 results for tenant_b
    assert len(store.query(query_vector=[1.0, 0.0], top_k=2, tenant_id="tenant_b")) == 0

    # contains_embedding_ids
    assert store.contains_embedding_ids(["e1", "e2", "e3"], tenant_id="tenant_a") == {"e1", "e2"}
    assert store.contains_embedding_ids(["e1", "e2"], tenant_id="tenant_b") == set()

    # delete_records_by_document_id
    assert store.delete_records_by_document_id("doc1", tenant_id="tenant_a") == 2
    assert len(store.query(query_vector=[1.0, 0.0], top_k=2, tenant_id="tenant_a")) == 0


def test_in_memory_store_metrics():
    for metric in ["cosine", "dot", "euclidean"]:
        store = InMemoryVectorStore()
        store.initialize_collection(CollectionConfig(dimension=2, distance_metric=metric))
        rec = EmbeddingRecord(
            embedding_id="e1",
            chunk_id="c1",
            document_id="d1",
            vector=[3.0, 4.0],
            dimension=2,
            provider_name="m",
            model_name="m",
            model_version="1",
            sanitized_content="c",
            semantic_key="k",
            tenant_id="t1",
        )
        store.upsert_records([rec], tenant_id="t1")
        res = store.query(query_vector=[3.0, 4.0], top_k=1, tenant_id="t1")
        assert len(res) == 1
        assert res[0].score > 0.0


def test_store_registry():
    store_cls = StoreRegistry.get("in_memory")
    assert store_cls == InMemoryVectorStore
    assert "in_memory" in StoreRegistry.list_stores()
