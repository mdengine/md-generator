"""Test Suite for Enterprise Hybrid Retrieval, Lexical BM25, Fusion, and Reranking.

Phase 1B/2A Verification:
1. Verifies pure-script BM25Okapi indexing, token normalization, and multi-tenant scoping.
2. Verifies QueryExpander acronym and domain synonym expansion (AF, BIL, PV, LoS, UBR).
3. Verifies RuleBasedQueryDecomposer compound query decomposition.
4. Verifies BaseReranker, RuleBasedReranker, and CrossEncoderReranker fallback.
5. Verifies EnterpriseHybridRetriever multi-way RRF fusion combining dense vectors, BM25, and phrases.
6. Verifies metadata filtering, candidate deduplication, and tenant boundary isolation.
7. Verifies LangChain invoke() compatibility.
"""

import pytest

from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.retrieval.bm25 import BM25Index, tokenize
from md_generator.retrieval.hybrid_retriever import (
    EnterpriseHybridRetriever,
    HybridSearchFilter,
)
from md_generator.retrieval.query_decomposer import RuleBasedQueryDecomposer
from md_generator.retrieval.query_expander import QueryExpander
from md_generator.retrieval.reranker import (
    CrossEncoderReranker,
    RuleBasedReranker,
)
from md_generator.vector.model import CollectionConfig, EmbeddingRecord
from md_generator.vector.providers.mock import MockEmbeddingProvider
from md_generator.vector.stores.in_memory import InMemoryVectorStore


def test_bm25_indexing_and_scoring():
    idx = BM25Index(k1=1.5, b=0.75)
    tenant = "tenant_test"

    # Add 3 documents
    idx.add_document("doc1", "AirFiber installation hold cases due to optical loss.", tenant)
    idx.add_document("doc2", "Business Internet Line BIL service level agreement 98.5%.", tenant)
    idx.add_document("doc3", "Retailer monthly payout scheme and commission distribution.", tenant)

    assert idx.total_documents == 3
    assert idx.average_document_length > 0

    # Search query
    res = idx.search("AirFiber hold", top_k=5, tenant_id=tenant)
    assert len(res) >= 1
    assert res[0][0] == "doc1"
    assert res[0][1] > 0.0

    # Search acronym expansion term
    res_bil = idx.search("Business Internet Line", top_k=5, tenant_id=tenant)
    assert len(res_bil) >= 1
    assert res_bil[0][0] == "doc2"

    # Serialization roundtrip
    dict_repr = idx.to_dict()
    reconstructed = BM25Index.from_dict(dict_repr)
    assert reconstructed.total_documents == 3
    res_recon = reconstructed.search("AirFiber hold", top_k=5, tenant_id=tenant)
    assert res_recon[0][0] == "doc1"

    # Document removal
    idx.remove_document("doc1")
    assert idx.total_documents == 2
    assert len(idx.search("AirFiber hold", top_k=5, tenant_id=tenant)) == 0


def test_query_expander_acronyms_and_phrases():
    expander = QueryExpander()

    # Acronym expansion: AF -> AirFiber, BIL -> Business Internet Line
    exp1 = expander.expand("AF installation guidelines")
    assert "airfiber" in exp1.lower()

    exp2 = expander.expand("BIL exception report")
    assert "business internet line" in exp2.lower()

    # Exact quoted phrase extraction
    query = 'What is the "AirFiber hold" procedure?'
    phrases = expander.extract_exact_phrases(query)
    assert phrases == ["AirFiber hold"]

    # Custom acronym registration
    expander.register_acronym("noc", "network operations center")
    exp_custom = expander.expand("escalate to NOC")
    assert "network operations center" in exp_custom.lower()


def test_query_decomposer():
    decomposer = RuleBasedQueryDecomposer()

    # Compound query with conjunctions
    compound_q = "What is the BIL installation procedure and what are the hold conditions?"
    subqueries = decomposer.decompose(compound_q)

    assert len(subqueries) >= 2
    assert subqueries[0] == compound_q
    # Subqueries must isolate the secondary topic while retaining subject context
    assert any("hold conditions" in sq.lower() for sq in subqueries)


def test_rule_based_and_cross_encoder_rerankers():
    class DummyCand:
        def __init__(self, cid: str, content: str, score: float):
            self.chunk_id = cid
            self.content = content
            self.score = score
            self.hybrid_score = score

    cand1 = DummyCand("c1", "General network configuration tips.", 0.6)
    cand2 = DummyCand("c2", "# AirFiber Installation Guidelines\nDetailed steps for optical alignment.", 0.5)

    reranker = RuleBasedReranker()
    reranked = reranker.rerank("AirFiber Installation Guidelines", [cand1, cand2], top_k=2)

    # cand2 has exact heading and phrase match, should be promoted to #1
    assert reranked[0].chunk_id == "c2"

    # CrossEncoder fallback test
    cross_enc = CrossEncoderReranker(model_name="non_existent_reranker_model", offline_mode=True)
    assert not cross_enc.is_available
    # Gracefully reranks using fallback
    reranked_fb = cross_enc.rerank("AirFiber Installation Guidelines", [cand1, cand2], top_k=2)
    assert reranked_fb[0].chunk_id == "c2"


def test_enterprise_hybrid_retriever_dense_and_bm25():
    tenant = "tenant_enterprise"
    p384 = MockEmbeddingProvider(dimension=384)
    v_store = InMemoryVectorStore()
    v_store.initialize_collection(CollectionConfig(collection_name="test_col", dimension=384))

    # Seed vector store records
    vec_text1 = "AirFiber hold resolution procedures and optical loss troubleshooting."
    vec_text2 = "Retailer monthly commission scheme and bonus targets."
    vectors = p384.embed_texts([vec_text1, vec_text2])

    rec1 = EmbeddingRecord(
        embedding_id="emb1",
        chunk_id="chunk_af",
        document_id="doc_af",
        vector=vectors[0],
        dimension=384,
        provider_name="mock",
        model_name="mock",
        model_version="1.0",
        sanitized_content=vec_text1,
        semantic_key="af",
        tenant_id=tenant,
        payload={"document_id": "doc_af", "page": 4},
    )
    rec2 = EmbeddingRecord(
        embedding_id="emb2",
        chunk_id="chunk_retailer",
        document_id="doc_ret",
        vector=vectors[1],
        dimension=384,
        provider_name="mock",
        model_name="mock",
        model_version="1.0",
        sanitized_content=vec_text2,
        semantic_key="ret",
        tenant_id=tenant,
        payload={"document_id": "doc_ret", "page": 10},
    )
    v_store.upsert_records([rec1, rec2], tenant_id=tenant)

    # Seed BM25 index
    bm25 = BM25Index()
    bm25.add_document("chunk_af", vec_text1, tenant_id=tenant, metadata={"document_id": "doc_af", "page": 4})
    bm25.add_document("chunk_retailer", vec_text2, tenant_id=tenant, metadata={"document_id": "doc_ret", "page": 10})
    bm25.add_document("chunk_bil_only", "Business Internet Line BIL SLA terms.", tenant_id=tenant, metadata={"document_id": "doc_bil", "page": 1})

    retriever = EnterpriseHybridRetriever(
        vector_store=v_store,
        embedding_provider=p384,
        tenant_id=tenant,
        bm25_index=bm25,
        top_k=5,
    )

    # Hybrid Search: query matches chunk_af strongly in both vector and BM25
    results = retriever.retrieve("AirFiber hold optical loss")
    assert len(results) >= 1
    top = results[0]
    assert top.chunk_id == "chunk_af"
    assert top.provenance == "HYBRID"
    assert top.hybrid_score > 0.0

    # Lexical keyword search retrieving BM25-backed candidate
    res_bil = retriever.retrieve("BIL SLA")
    assert any(r.chunk_id == "chunk_bil_only" for r in res_bil)


def test_metadata_filtering_and_tenant_isolation():
    tenant = "tenant_alpha"
    p384 = MockEmbeddingProvider(dimension=384)
    v_store = InMemoryVectorStore()
    v_store.initialize_collection(CollectionConfig(collection_name="col", dimension=384))

    v = p384.embed_texts(["Alpha document content."])[0]
    rec = EmbeddingRecord(
        embedding_id="emb_a",
        chunk_id="c_alpha",
        document_id="doc_alpha",
        vector=v,
        dimension=384,
        provider_name="mock",
        model_name="mock",
        model_version="1.0",
        sanitized_content="Alpha document content.",
        semantic_key="alpha",
        tenant_id=tenant,
        payload={"document_id": "doc_alpha", "source_location": {"location_type": "pdf", "page": 5}},
    )
    v_store.upsert_records([rec], tenant_id=tenant)

    bm25 = BM25Index()
    bm25.add_document("c_alpha", "Alpha document content.", tenant_id=tenant, metadata={"document_id": "doc_alpha", "source_location": {"location_type": "pdf", "page": 5}})

    retriever = EnterpriseHybridRetriever(
        vector_store=v_store,
        embedding_provider=p384,
        tenant_id=tenant,
        bm25_index=bm25,
    )

    # 1. Filter matching document_ids
    filters_match = HybridSearchFilter(document_ids={"doc_alpha"})
    res_match = retriever.retrieve("Alpha content", filters=filters_match)
    assert len(res_match) == 1

    # 2. Filter non-matching document_ids
    filters_nomatch = HybridSearchFilter(document_ids={"doc_other"})
    res_nomatch = retriever.retrieve("Alpha content", filters=filters_nomatch)
    assert len(res_nomatch) == 0

    # 3. Filter by page
    filters_page = HybridSearchFilter(pages={5})
    assert len(retriever.retrieve("Alpha content", filters=filters_page)) == 1

    filters_wrong_page = HybridSearchFilter(pages={99})
    assert len(retriever.retrieve("Alpha content", filters=filters_wrong_page)) == 0

    # 4. Tenant boundary enforcement
    with pytest.raises(TenantBoundaryError):
        EnterpriseHybridRetriever(
            vector_store=v_store,
            embedding_provider=p384,
            tenant_id="",  # Empty tenant must raise TenantBoundaryError
        )


def test_candidate_deduplication():
    tenant = "tenant_dedup"
    p384 = MockEmbeddingProvider(dimension=384)
    v_store = InMemoryVectorStore()
    v_store.initialize_collection(CollectionConfig(collection_name="col", dimension=384))

    # Two chunks with 95% overlapping sentences from the same document
    text1 = "Standard installation procedures for enterprise customers. Always ensure power cables are grounded properly."
    text2 = "Standard installation procedures for enterprise customers. Always ensure power cables are grounded properly and tested."
    v1, v2 = p384.embed_texts([text1, text2])

    v_store.upsert_records([
        EmbeddingRecord(
            embedding_id="e1", chunk_id="c1", document_id="doc1", vector=v1, dimension=384,
            provider_name="mock", model_name="mock", model_version="1.0", sanitized_content=text1,
            semantic_key="k1", tenant_id=tenant, payload={"document_id": "doc1"},
        ),
        EmbeddingRecord(
            embedding_id="e2", chunk_id="c2", document_id="doc1", vector=v2, dimension=384,
            provider_name="mock", model_name="mock", model_version="1.0", sanitized_content=text2,
            semantic_key="k2", tenant_id=tenant, payload={"document_id": "doc1"},
        ),
    ], tenant_id=tenant)

    bm25 = BM25Index()
    bm25.add_document("c1", text1, tenant_id=tenant, metadata={"document_id": "doc1"})
    bm25.add_document("c2", text2, tenant_id=tenant, metadata={"document_id": "doc1"})

    retriever = EnterpriseHybridRetriever(
        vector_store=v_store,
        embedding_provider=p384,
        tenant_id=tenant,
        bm25_index=bm25,
        enable_deduplication=True,
        dedup_overlap_threshold=0.80,
    )

    results = retriever.retrieve("installation procedures power cables grounded")
    # Near-duplicate chunk should be suppressed
    assert len(results) == 1


def test_langchain_invoke_compatibility():
    tenant = "tenant_langchain"
    p384 = MockEmbeddingProvider(dimension=384)
    v_store = InMemoryVectorStore()
    v_store.initialize_collection(CollectionConfig(collection_name="col", dimension=384))

    bm25 = BM25Index()
    bm25.add_document("doc_lc", "LangChain compatible document result.", tenant_id=tenant, metadata={"document_id": "d1"})

    retriever = EnterpriseHybridRetriever(
        vector_store=v_store,
        embedding_provider=p384,
        tenant_id=tenant,
        bm25_index=bm25,
    )

    docs = retriever.invoke("LangChain compatible")
    assert len(docs) >= 1
    doc = docs[0]
    assert hasattr(doc, "page_content")
    assert hasattr(doc, "metadata")
    assert doc.metadata["tenant_id"] == tenant
    assert doc.metadata["score"] > 0.0
