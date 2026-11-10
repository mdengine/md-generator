"""Tests for PromptContextBuilder adapter component."""

import math
import pytest
from langchain_core.documents import Document

from md_generator.adapters.langchain.context import (
    PromptContextBuilder,
    canonical_document_fingerprint,
    extract_and_validate_score,
    estimate_token_count,
)


def _make_doc(content: str, score: float = 0.5, **metadata_kwargs) -> Document:
    meta = {"score": score}
    meta.update(metadata_kwargs)
    return Document(page_content=content, metadata=meta)


# ==============================================================================
# Hardening Requirement A: Truly Canonical Fingerprinting Tests
# ==============================================================================

def test_fingerprint_nested_metadata_key_order_invariance():
    """Validates that dictionary insertion order differences produce identical fingerprints."""
    meta1 = {
        "b": 2,
        "a": 1,
        "nested": {"z": 100, "y": 200, "deep": {"k2": "val2", "k1": "val1"}},
    }
    meta2 = {
        "nested": {"deep": {"k1": "val1", "k2": "val2"}, "y": 200, "z": 100},
        "a": 1,
        "b": 2,
    }
    doc1 = Document(page_content="test content", metadata=meta1)
    doc2 = Document(page_content="test content", metadata=meta2)

    fp1 = canonical_document_fingerprint(doc1)
    fp2 = canonical_document_fingerprint(doc2)
    assert fp1 == fp2, "Fingerprints must be identical regardless of dictionary key insertion order"


def test_fingerprint_preserves_type_distinctions():
    """Validates that type distinctions (e.g., int vs str, bool vs int) produce distinct fingerprints."""
    doc_int = Document(page_content="same", metadata={"val": 1})
    doc_str = Document(page_content="same", metadata={"val": "1"})
    doc_bool = Document(page_content="same", metadata={"val": True})
    doc_none = Document(page_content="same", metadata={"val": None})

    fps = {
        "int": canonical_document_fingerprint(doc_int),
        "str": canonical_document_fingerprint(doc_str),
        "bool": canonical_document_fingerprint(doc_bool),
        "none": canonical_document_fingerprint(doc_none),
    }
    # All fingerprints must be unique
    assert len(set(fps.values())) == 4, f"Type distinctions must yield distinct fingerprints: {fps}"


def test_fingerprint_memory_address_independence():
    """Validates that custom objects with volatile memory addresses produce deterministic fingerprints."""
    class CustomObj:
        def __init__(self, name):
            self.name = name

    obj1 = CustomObj("entity-A")
    obj2 = CustomObj("entity-A")  # Different memory address

    doc1 = Document(page_content="text", metadata={"obj": obj1})
    doc2 = Document(page_content="text", metadata={"obj": obj2})

    fp1 = canonical_document_fingerprint(doc1)
    fp2 = canonical_document_fingerprint(doc2)
    assert fp1 == fp2, "Fingerprints must be independent of Python object memory addresses"


# ==============================================================================
# Hardening Requirement B: Extreme Numeric Score Validation & Overflow Tests
# ==============================================================================

def test_extract_and_validate_score_valid():
    """Validates extraction of standard integer and float scores."""
    assert extract_and_validate_score(Document(page_content="x", metadata={"score": 0.85})) == 0.85
    assert extract_and_validate_score(Document(page_content="x", metadata={"score": 1})) == 1.0
    assert extract_and_validate_score(Document(page_content="x", metadata={"score": 0})) == 0.0


def test_extract_and_validate_score_overflow():
    """Validates that extreme integer scores causing float conversion overflow raise ValueError."""
    huge_int = 10**400
    doc = Document(page_content="x", metadata={"score": huge_int})
    with pytest.raises(ValueError, match="overflow"):
        extract_and_validate_score(doc)


@pytest.mark.parametrize("invalid_score", [
    float("nan"),
    float("inf"),
    float("-inf"),
    True,
    False,
    "0.95",
    [0.95],
    None,
])
def test_extract_and_validate_score_invalid_values(invalid_score):
    """Validates that non-numeric, boolean, NaN, and Inf values raise ValueError."""
    doc = Document(page_content="x", metadata={"score": invalid_score})
    with pytest.raises(ValueError):
        extract_and_validate_score(doc)


# ==============================================================================
# 4 Core Review Test Scenarios: Deterministic Tie-Breaking & Ordering
# ==============================================================================

def test_deduplication_equal_score_deterministic_tie_break():
    """Scenario 1: Equal-score duplicate candidates supplied in reversed input orders retain same candidate."""
    builder = PromptContextBuilder()
    doc_a = _make_doc("candidate content Alpha", score=0.85, chunk_id="chunk-shared-01")
    doc_b = _make_doc("candidate content Beta", score=0.85, chunk_id="chunk-shared-01")

    res_forward = builder.deduplicate_documents([doc_a, doc_b])
    res_reversed = builder.deduplicate_documents([doc_b, doc_a])

    assert len(res_forward) == 1
    assert len(res_reversed) == 1
    assert res_forward[0].page_content == res_reversed[0].page_content


def test_order_documents_identical_five_level_sort_keys():
    """Scenario 2: Distinct documents with identical five-level sort keys produce same final ordering."""
    builder = PromptContextBuilder()
    doc_1 = _make_doc(
        "Content 1",
        score=0.9,
        parent_chunk_id=None,
        document_id="doc-001",
        source_location={"line_start": 10},
        chunk_id="chunk-001",
    )
    doc_2 = _make_doc(
        "Content 2",
        score=0.9,
        parent_chunk_id=None,
        document_id="doc-001",
        source_location={"line_start": 10},
        chunk_id="chunk-001",
    )

    res_1 = builder.order_documents([doc_1, doc_2])
    res_2 = builder.order_documents([doc_2, doc_1])

    order_1 = [d.page_content for d in res_1]
    order_2 = [d.page_content for d in res_2]
    assert order_1 == order_2


def test_unkeyed_documents_shuffled_byte_identical_context():
    """Scenario 3: Unkeyed documents supplied in different orders produce byte-identical context output."""
    builder = PromptContextBuilder(include_citations=False)
    u1 = _make_doc("Unkeyed document section AAA", score=0.7)
    u2 = _make_doc("Unkeyed document section BBB", score=0.7)
    u3 = _make_doc("Unkeyed document section CCC", score=0.8)

    context_1 = builder.build_context([u1, u2, u3])
    context_2 = builder.build_context([u3, u1, u2])
    context_3 = builder.build_context([u2, u3, u1])

    assert context_1 == context_2 == context_3
    assert len(context_1) > 0


def test_deduplication_retains_highest_score():
    """Validates that candidate with highest relevance score is retained order-independently."""
    builder = PromptContextBuilder()
    doc_low = _make_doc("low score chunk", score=0.60, chunk_id="chunk-A")
    doc_mid = _make_doc("mid score chunk", score=0.75, chunk_id="chunk-B")
    doc_high = _make_doc("high score chunk", score=0.92, chunk_id="chunk-A")

    res_1 = builder.deduplicate_documents([doc_low, doc_mid, doc_high])
    res_2 = builder.deduplicate_documents([doc_high, doc_low, doc_mid])

    # Should retain doc_high for chunk-A and doc_mid for chunk-B
    assert len(res_1) == 2
    assert len(res_2) == 2

    by_chunk_1 = {d.metadata["chunk_id"]: d.metadata["score"] for d in res_1}
    by_chunk_2 = {d.metadata["chunk_id"]: d.metadata["score"] for d in res_2}
    assert by_chunk_1 == {"chunk-A": 0.92, "chunk-B": 0.75}
    assert by_chunk_2 == {"chunk-A": 0.92, "chunk-B": 0.75}


def test_deduplication_collision_safe_tuple_keys():
    """Validates delimiter collision safety with tuple keys."""
    builder = PromptContextBuilder()
    # If concatenated with ":", "doc:1" + "key:2" == "doc" + "1:key:2" -> collision!
    doc1 = _make_doc("content 1", score=0.8, document_id="doc:1", semantic_key="key:2")
    doc2 = _make_doc("content 2", score=0.8, document_id="doc", semantic_key="1:key:2")

    res = builder.deduplicate_documents([doc1, doc2])
    assert len(res) == 2, "Tuple keys must prevent delimiter collisions"


def test_deduplication_preserves_unkeyed_documents():
    """Validates that documents lacking identity keys are preserved without being collapsed."""
    builder = PromptContextBuilder()
    u1 = _make_doc("Unkeyed 1", score=0.5)
    u2 = _make_doc("Unkeyed 2", score=0.5)
    u3 = _make_doc("Unkeyed 3", score=0.5)

    res = builder.deduplicate_documents([u1, u2, u3])
    assert len(res) == 3


# ==============================================================================
# Token Budgeting & Estimator Validation Tests
# ==============================================================================

def test_token_budget_estimation():
    """Validates that synthesized prompt does not exceed max_tokens."""
    builder = PromptContextBuilder(max_tokens=30)
    docs = [
        _make_doc(f"This is a longer paragraph for chunk {i} with several words and tokens.", score=0.9 - i * 0.1)
        for i in range(10)
    ]
    prompt = builder.build_context(docs)
    total_tokens = estimate_token_count(prompt)
    assert total_tokens <= 30


def test_token_estimator_type_validation():
    """Validates that token estimator returning non-integer or negative values raises ValueError."""
    def bad_estimator_float(text):
        return 12.5

    def bad_estimator_bool(text):
        return True

    def bad_estimator_negative(text):
        return -5

    builder_float = PromptContextBuilder(token_estimator=bad_estimator_float)
    builder_bool = PromptContextBuilder(token_estimator=bad_estimator_bool)
    builder_neg = PromptContextBuilder(token_estimator=bad_estimator_negative)

    doc = _make_doc("text", score=0.8)
    with pytest.raises(ValueError, match="token_estimator must return a non-negative integer"):
        builder_float.build_context([doc])

    with pytest.raises(ValueError, match="token_estimator must return a non-negative integer"):
        builder_bool.build_context([doc])

    with pytest.raises(ValueError, match="token_estimator must return a non-negative integer"):
        builder_neg.build_context([doc])


def test_sanitized_content_invariant():
    """Validates that raw secrets or unredacted fields are never reconstructed into the prompt."""
    builder = PromptContextBuilder(include_citations=True)
    doc = _make_doc(
        "Safe sanitized content [REDACTED_API_KEY]",
        score=0.95,
        document_id="doc-safe",
        chunk_id="chunk-safe",
        source_location={"path": "src/main.py", "line_start": 5, "line_end": 10},
    )
    prompt = builder.build_context([doc])
    assert "Safe sanitized content [REDACTED_API_KEY]" in prompt
    assert "Location: src/main.py:5-10" in prompt
    assert "password" not in prompt
    assert "secret" not in prompt


def test_builder_empty_documents():
    """Validates that empty document lists return empty prompt string."""
    builder = PromptContextBuilder()
    assert builder.build_context([]) == ""
