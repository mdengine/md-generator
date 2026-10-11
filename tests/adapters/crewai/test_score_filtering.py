"""Tests for MDSearchTool score validation, boundary conditions, and vector-store metric normalization (P2B-R04)."""

import math
from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from md_generator.adapters.crewai import MDSearchTool
from md_generator.adapters.crewai.exceptions import CrewAIToolExecutionError
from md_generator.adapters.langchain.retriever import MDVectorStoreRetriever
from md_generator.vector.model import CollectionConfig, EmbeddingRecord
from md_generator.vector.stores.in_memory import InMemoryVectorStore


@pytest.mark.parametrize("valid_score", [0.0, 0.5, 1.0, 0, 1])
def test_tool_construction_valid_min_score(valid_score):
    """Valid numeric thresholds within [0.0, 1.0] are accepted."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=valid_score)
    assert tool.min_score == float(valid_score)


@pytest.mark.parametrize(
    "invalid_score,error_match",
    [
        (True, "min_score cannot be a boolean"),
        (False, "min_score cannot be a boolean"),
        ("0.5", "must be a numeric float or int"),
        (None, "must be a numeric float or int"),
        (float("nan"), "cannot be NaN or Infinite"),
        (float("inf"), "cannot be NaN or Infinite"),
        (float("-inf"), "cannot be NaN or Infinite"),
        (-0.1, r"must be between 0\.0 and 1\.0"),
        (-1e-6, r"must be between 0\.0 and 1\.0"),
        (1.0001, r"must be between 0\.0 and 1\.0"),
        (1.1, r"must be between 0\.0 and 1\.0"),
    ],
)
def test_tool_construction_invalid_min_score_rejected(invalid_score, error_match):
    """Invalid threshold types, booleans, strings, non-finites, and out-of-bound values raise ValueError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    with pytest.raises(ValueError, match=error_match):
        MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=invalid_score)


@pytest.mark.parametrize("boundary_score", [0.0, 1.0, 0.000001, 0.999999])
def test_tool_execution_accepts_exact_boundary_scores(boundary_score):
    """Retrieved document scores at exact boundaries 0.0, 1.0, and near-boundaries are valid (P2B-R04)."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(
            page_content="Boundary Score Doc",
            metadata={"tenant_id": "tenant-prod", "score": boundary_score, "document_id": "doc1"},
        ),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.0)
    result = tool.run(query="search")
    assert "Boundary Score Doc" in result


@pytest.mark.parametrize(
    "bad_doc_score,error_match",
    [
        (None, "has None 'score'"),
        (True, "has boolean 'score'"),
        (False, "has boolean 'score'"),
        ("0.9", "has non-numeric score"),
        (float("nan"), "has non-finite score"),
        (float("inf"), "has non-finite score"),
        (float("-inf"), "has non-finite score"),
        (-0.1, r"outside \[0\.0, 1\.0\]"),
        (-1e-7, r"outside \[0\.0, 1\.0\]"),
        (1.00001, r"outside \[0\.0, 1\.0\]"),
        (1.1, r"outside \[0\.0, 1\.0\]"),
    ],
)
def test_tool_execution_rejects_invalid_document_scores(bad_doc_score, error_match):
    """Retrieved document with invalid score type, boolean, non-finite, or out-of-bounds raises CrewAIToolExecutionError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="Bad Score Doc", metadata={"tenant_id": "tenant-prod", "score": bad_doc_score}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.0)
    with pytest.raises(CrewAIToolExecutionError, match=error_match):
        tool.run(query="search")


def test_tool_execution_rejects_missing_document_score():
    """Retrieved document missing 'score' key entirely raises CrewAIToolExecutionError."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="No Score Doc", metadata={"tenant_id": "tenant-prod"}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.5)
    with pytest.raises(CrewAIToolExecutionError, match="missing mandatory 'score'"):
        tool.run(query="search")


def test_tool_filters_documents_below_threshold():
    """Documents strictly below min_score are filtered out before context synthesis."""
    mock_retriever = MagicMock()
    mock_retriever.tenant_id = "tenant-prod"
    mock_retriever.invoke.return_value = [
        Document(page_content="High Relevance Doc", metadata={"tenant_id": "tenant-prod", "score": 0.90, "document_id": "doc1"}),
        Document(page_content="Low Relevance Doc", metadata={"tenant_id": "tenant-prod", "score": 0.60, "document_id": "doc2"}),
    ]

    tool = MDSearchTool(retriever=mock_retriever, tenant_id="tenant-prod", min_score=0.80)
    result = tool.run(query="search")

    assert "High Relevance Doc" in result
    assert "Low Relevance Doc" not in result


# --- Real Vector Store Distance Metric Score Compatibility Tests (P2B-R04) ---

class DummyProvider:
    def __init__(self, vector: list):
        self.vector = vector
        self.dimension = len(vector)

    def embed_texts(self, texts):
        return [self.vector for _ in texts]


def test_metric_score_compatibility_euclidean():
    """Euclidean distance metric computes 1 / (1 + dist), which is naturally bounded in (0.0, 1.0]."""
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(collection_name="test_euc", dimension=2, distance_metric="euclidean"))
    store.upsert_records(
        [
            EmbeddingRecord(
                embedding_id="rec1",
                chunk_id="chunk1",
                document_id="doc1",
                vector=[1.0, 0.0],
                dimension=2,
                provider_name="dummy",
                model_name="dummy",
                model_version="1.0",
                semantic_key="doc1:chunk1",
                tenant_id="tenant-metric",
                sanitized_content="Euclidean Content",
            )
        ],
        tenant_id="tenant-metric",
    )
    provider = DummyProvider([1.0, 0.0])  # identical vector -> dist=0 -> score=1.0
    retriever = MDVectorStoreRetriever(store=store, provider=provider, tenant_id="tenant-metric", top_k=1)

    tool = MDSearchTool(retriever=retriever, tenant_id="tenant-metric", min_score=0.5)
    result = tool.run(query="test")
    assert "Euclidean Content" in result


def test_metric_score_compatibility_cosine_non_negative():
    """Cosine similarity on standard positive embeddings produces scores in [0.0, 1.0] and passes."""
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(collection_name="test_cos", dimension=2, distance_metric="cosine"))
    store.upsert_records(
        [
            EmbeddingRecord(
                embedding_id="rec1",
                chunk_id="chunk1",
                document_id="doc1",
                vector=[1.0, 1.0],
                dimension=2,
                provider_name="dummy",
                model_name="dummy",
                model_version="1.0",
                semantic_key="doc1:chunk1",
                tenant_id="tenant-metric",
                sanitized_content="Cosine Acute Content",
            )
        ],
        tenant_id="tenant-metric",
    )
    provider = DummyProvider([1.0, 0.0])  # angle 45 deg -> cos = 1/sqrt(2) approx 0.707
    retriever = MDVectorStoreRetriever(store=store, provider=provider, tenant_id="tenant-metric", top_k=1)

    tool = MDSearchTool(retriever=retriever, tenant_id="tenant-metric", min_score=0.5)
    result = tool.run(query="test")
    assert "Cosine Acute Content" in result


def test_metric_score_compatibility_cosine_negative_rejection():
    """Cosine similarity on opposing vectors produces negative score (< 0.0), raising CrewAIToolExecutionError."""
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(collection_name="test_cos_neg", dimension=2, distance_metric="cosine"))
    store.upsert_records(
        [
            EmbeddingRecord(
                embedding_id="rec1",
                chunk_id="chunk1",
                document_id="doc1",
                vector=[-1.0, 0.0],  # opposite direction
                dimension=2,
                provider_name="dummy",
                model_name="dummy",
                model_version="1.0",
                semantic_key="doc1:chunk1",
                tenant_id="tenant-metric",
                sanitized_content="Cosine Opposite Content",
            )
        ],
        tenant_id="tenant-metric",
    )
    provider = DummyProvider([1.0, 0.0])  # query vector [1, 0] -> dot = -1 -> score = -1.0
    retriever = MDVectorStoreRetriever(store=store, provider=provider, tenant_id="tenant-metric", top_k=1)

    tool = MDSearchTool(retriever=retriever, tenant_id="tenant-metric", min_score=0.0)
    with pytest.raises(CrewAIToolExecutionError, match=r"score -1\.0 is outside \[0\.0, 1\.0\]"):
        tool.run(query="test")


def test_metric_score_compatibility_dot_unnormalized_rejection():
    """Dot product on unnormalized vectors can produce score > 1.0, which raises CrewAIToolExecutionError."""
    store = InMemoryVectorStore()
    store.initialize_collection(CollectionConfig(collection_name="test_dot_large", dimension=2, distance_metric="dot"))
    store.upsert_records(
        [
            EmbeddingRecord(
                embedding_id="rec1",
                chunk_id="chunk1",
                document_id="doc1",
                vector=[5.0, 5.0],  # unnormalized vector
                dimension=2,
                provider_name="dummy",
                model_name="dummy",
                model_version="1.0",
                semantic_key="doc1:chunk1",
                tenant_id="tenant-metric",
                sanitized_content="Dot Large Content",
            )
        ],
        tenant_id="tenant-metric",
    )
    provider = DummyProvider([2.0, 2.0])  # query vector [2, 2] -> dot = 10 + 10 = 20.0
    retriever = MDVectorStoreRetriever(store=store, provider=provider, tenant_id="tenant-metric", top_k=1)

    tool = MDSearchTool(retriever=retriever, tenant_id="tenant-metric", min_score=0.0)
    with pytest.raises(CrewAIToolExecutionError, match=r"score 20\.0 is outside \[0\.0, 1\.0\]"):
        tool.run(query="test")
