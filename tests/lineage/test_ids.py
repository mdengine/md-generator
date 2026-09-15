"""Contract Tests for Deterministic Identity & Lineage ID Generation."""

import pytest
from md_generator.semantic.model.schema import InvalidSchemaError
from md_generator.lineage import (
    normalize_source_uri,
    generate_canonical_json,
    compute_content_hash,
    generate_document_id,
    generate_revision_id,
    canonicalize_semantic_key,
    generate_chunk_id,
)


def test_normalize_source_uri():
    # Windows drive letter standardization & slash normalization
    assert normalize_source_uri("C:\\Task\\Project\\main.py") == "c:/Task/Project/main.py"
    # Linux path slash preservation
    assert normalize_source_uri("/usr/src/app/main.py") == "/usr/src/app/main.py"


def test_document_id_determinism():
    doc_id1 = generate_document_id("file:///src/main.py", "code", "org/repo")
    doc_id2 = generate_document_id("file:///src/main.py", "code", "org/repo")
    assert doc_id1 == doc_id2
    assert len(doc_id1) == 64

    # Different repository yields different document_id
    doc_id3 = generate_document_id("file:///src/main.py", "code", "other/repo")
    assert doc_id1 != doc_id3


def test_revision_id_determinism():
    doc_id = generate_document_id("file:///src/main.py", "code", "org/repo")
    content_hash = compute_content_hash("def foo(): pass")

    rev_id1 = generate_revision_id(doc_id, content_hash, commit="commit_100")
    rev_id2 = generate_revision_id(doc_id, content_hash, commit="commit_100")
    assert rev_id1 == rev_id2
    assert len(rev_id1) == 64

    # Content change yields different revision_id for same document_id
    content_hash2 = compute_content_hash("def foo(): return 42")
    rev_id3 = generate_revision_id(doc_id, content_hash2, commit="commit_100")
    assert rev_id1 != rev_id3


def test_semantic_key_canonicalization():
    key = canonicalize_semantic_key("class", "com.company.PaymentService")
    assert key == "class:com.company.PaymentService"

    key_openapi = canonicalize_semantic_key("endpoint", "POST:/payments")
    assert key_openapi == "endpoint:POST:/payments"


def test_chunk_id_semantic_determinism():
    doc_id = generate_document_id("file:///src/main.py", "code", "org/repo")
    sem_key = canonicalize_semantic_key("method", "PaymentService.processPayment")
    chunk_hash = compute_content_hash("public void processPayment() {}")

    chunk_id1 = generate_chunk_id(doc_id, sem_key, chunk_hash)
    chunk_id2 = generate_chunk_id(doc_id, sem_key, chunk_hash)
    assert chunk_id1 == chunk_id2
    assert len(chunk_id1) == 64

    # Semantic content change yields different chunk_id
    chunk_hash2 = compute_content_hash("public void processPayment() { log.info(); }")
    chunk_id3 = generate_chunk_id(doc_id, sem_key, chunk_hash2)
    assert chunk_id1 != chunk_id3
