"""Tests for MDVectorStoreRetriever adapter component."""

import pytest
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.stores.in_memory import InMemoryVectorStore
from md_generator.vector.model import CollectionConfig, EmbeddingRecord, VectorQueryResult
from md_generator.vector.exceptions import TenantBoundaryError, VectorError
from md_generator.adapters.langchain.retriever import MDVectorStoreRetriever
from md_generator.adapters.langchain.exceptions import LangChainAdapterError


def _setup_store_and_provider(dimension: int = 8):
    provider = MockEmbeddingProvider(dimension=dimension)
    store = InMemoryVectorStore()
    cfg = CollectionConfig(collection_name="test_lc_retriever", dimension=dimension)
    store.initialize_collection(cfg)
    return store, provider


def test_retriever_subclasses_base_retriever():
    """Validates that MDVectorStoreRetriever subclasses LangChain's BaseRetriever."""
    assert issubclass(MDVectorStoreRetriever, BaseRetriever)


def test_retriever_tenant_immutability():
    """Validates that post-construction modification of tenant_id is rejected."""
    store, provider = _setup_store_and_provider()
    retriever = MDVectorStoreRetriever(
        store=store,
        provider=provider,
        tenant_id="tenant-immutable",
        top_k=3,
    )
    with pytest.raises((TenantBoundaryError, AttributeError, Exception)):
        retriever.tenant_id = "tenant-tampered"


def test_retriever_runtime_tenant_override_rejected():
    """Validates that passing tenant_id to invoke() raises TenantBoundaryError."""
    store, provider = _setup_store_and_provider()
    retriever = MDVectorStoreRetriever(
        store=store,
        provider=provider,
        tenant_id="tenant-alpha",
        top_k=3,
    )
    with pytest.raises(TenantBoundaryError, match="Runtime tenant_id override is prohibited"):
        retriever.invoke("search query", tenant_id="tenant-spoofed")


def test_retriever_top_k_validation():
    """Validates top_k bounds validation."""
    store, provider = _setup_store_and_provider()
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        MDVectorStoreRetriever(
            store=store,
            provider=provider,
            tenant_id="tenant-alpha",
            top_k=0,
        )

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        MDVectorStoreRetriever(
            store=store,
            provider=provider,
            tenant_id="tenant-alpha",
            top_k=-5,
        )


def test_retriever_empty_tenant_validation():
    """Validates tenant_id non-empty string validation."""
    store, provider = _setup_store_and_provider()
    with pytest.raises(TenantBoundaryError, match="requires a valid non-empty tenant_id"):
        MDVectorStoreRetriever(
            store=store,
            provider=provider,
            tenant_id="",
        )

    with pytest.raises(TenantBoundaryError, match="requires a valid non-empty tenant_id"):
        MDVectorStoreRetriever(
            store=store,
            provider=provider,
            tenant_id="   ",
        )


def test_retriever_empty_query_validation():
    """Validates query non-empty string validation."""
    store, provider = _setup_store_and_provider()
    retriever = MDVectorStoreRetriever(
        store=store,
        provider=provider,
        tenant_id="tenant-alpha",
    )
    with pytest.raises(ValueError, match="Query must be a non-empty string"):
        retriever.invoke("")

    with pytest.raises(ValueError, match="Query must be a non-empty string"):
        retriever.invoke("   ")


def test_retriever_lifecycle_invocation():
    """Validates full retrieval lifecycle: embed query -> store query -> return Documents."""
    store, provider = _setup_store_and_provider(dimension=8)
    tenant = "tenant-prod"

    # Upsert test records
    vec1 = provider.embed_texts(["first chunk"])[0]
    vec2 = provider.embed_texts(["second chunk"])[0]
    rec1 = EmbeddingRecord(
        embedding_id="e1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
        chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
        document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
        vector=vec1,
        dimension=8,
        provider_name="mock",
        model_name="mock-model",
        model_version="1.0",
        sanitized_content="first chunk content",
        semantic_key="test.key.1",
        tenant_id=tenant,
        payload={"document_id": "doc-provenance-001", "author": "Alice"},
    )
    rec2 = EmbeddingRecord(
        embedding_id="e1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        vector=vec2,
        dimension=8,
        provider_name="mock",
        model_name="mock-model",
        model_version="1.0",
        sanitized_content="second chunk content",
        semantic_key="test.key.2",
        tenant_id=tenant,
        payload={"document_id": "doc-provenance-002", "author": "Bob"},
    )
    store.upsert_records([rec1, rec2], tenant_id=tenant)

    retriever = MDVectorStoreRetriever(
        store=store,
        provider=provider,
        tenant_id=tenant,
        top_k=2,
    )

    docs = retriever.invoke("first chunk")
    assert isinstance(docs, list)
    assert len(docs) == 2
    for doc in docs:
        assert isinstance(doc, Document)
        assert doc.metadata["tenant_id"] == tenant

    # Check document_id provenance from payload
    doc_ids = {d.metadata["document_id"] for d in docs}
    assert "doc-provenance-001" in doc_ids
    assert "doc-provenance-002" in doc_ids

    # Check payload extra metadata merged
    authors = {d.metadata.get("author") for d in docs}
    assert "Alice" in authors
    assert "Bob" in authors


def test_retriever_score_ranking_preserved():
    """Validates that relevance score ranking from vector store is strictly preserved."""
    store, provider = _setup_store_and_provider(dimension=8)
    tenant = "tenant-rank"

    # Pre-embed
    vec1 = provider.embed_texts(["high similarity query match"])[0]
    vec2 = provider.embed_texts(["completely unrelated text zzzz"])[0]

    rec1 = EmbeddingRecord(
        embedding_id="e1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
        chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
        document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b1",
        vector=vec1,
        dimension=8,
        provider_name="mock",
        model_name="mock-model",
        model_version="1.0",
        sanitized_content="high match",
        semantic_key="test.key.rank1",
        tenant_id=tenant,
    )
    rec2 = EmbeddingRecord(
        embedding_id="e1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        chunk_id="c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        document_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        vector=vec2,
        dimension=8,
        provider_name="mock",
        model_name="mock-model",
        model_version="1.0",
        sanitized_content="low match",
        semantic_key="test.key.rank2",
        tenant_id=tenant,
    )
    store.upsert_records([rec1, rec2], tenant_id=tenant)

    retriever = MDVectorStoreRetriever(
        store=store,
        provider=provider,
        tenant_id=tenant,
        top_k=2,
    )

    docs = retriever.invoke("high similarity query match")
    assert len(docs) == 2
    assert docs[0].metadata["score"] >= docs[1].metadata["score"]
    assert docs[0].page_content == "high match"


def test_retriever_error_translation():
    """Validates error translation when underlying provider or store fails."""
    store, provider = _setup_store_and_provider(dimension=8)

    class FailingProvider:
        dimension = 8
        def embed_texts(self, texts):
            raise RuntimeError("Provider connection timeout")

    retriever = MDVectorStoreRetriever(
        store=store,
        provider=FailingProvider(),
        tenant_id="tenant-err",
    )
    with pytest.raises(LangChainAdapterError, match="Retriever query failed"):
        retriever.invoke("test query")
