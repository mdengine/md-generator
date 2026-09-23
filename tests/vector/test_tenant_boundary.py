"""Unit tests for mandatory tenant isolation and boundary error enforcement."""

import pytest
from md_generator.vector.exceptions import TenantBoundaryError
from md_generator.vector.model import CollectionConfig, EmbeddingRecord
from md_generator.vector.stores.in_memory import InMemoryVectorStore


def test_tenant_omission_protocol_signature_typeerror():
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig())

    # Omitting tenant_id at Python protocol boundary produces TypeError
    with pytest.raises(TypeError):
        store.upsert_records([])  # type: ignore

    with pytest.raises(TypeError):
        store.query(query_vector=[0.1, 0.2], top_k=2)  # type: ignore

    with pytest.raises(TypeError):
        store.delete_records_by_document_id("doc1")  # type: ignore


def test_tenant_explicit_none_or_empty_tenant_boundary_error():
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig())

    with pytest.raises(TenantBoundaryError):
        store.upsert_records([], tenant_id=None)  # type: ignore

    with pytest.raises(TenantBoundaryError):
        store.upsert_records([], tenant_id="")

    with pytest.raises(TenantBoundaryError):
        store.query(query_vector=[0.1, 0.2], top_k=2, tenant_id="")


def test_cross_tenant_record_mismatch_tenant_boundary_error():
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(dimension=2))

    record = EmbeddingRecord(
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

    with pytest.raises(TenantBoundaryError, match="does not match operation tenant_id"):
        store.upsert_records([record], tenant_id="tenant_b")
