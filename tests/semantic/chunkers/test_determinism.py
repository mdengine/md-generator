"""Tests for AST parsing determinism and semantic key stability."""

import hashlib
from md_generator.semantic.processor import SemanticProcessor
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_semantic_processing_determinism():
    processor = SemanticProcessor()
    code = "class Payment:\n    def pay(self):\n        pass\n"
    doc_id = _make_doc_id("doc-det-1")

    doc1 = SemanticDocument(
        document_id=doc_id,
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///payment.py", source_type="py", language="python"),
    )

    doc2 = SemanticDocument(
        document_id=doc_id,
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///payment.py", source_type="py", language="python"),
    )

    res1 = processor.process_documents([doc1])
    res2 = processor.process_documents([doc2])

    assert [c.chunk_id for c in res1.chunks] == [c.chunk_id for c in res2.chunks]
    assert [e.entity_id for e in res1.entities] == [e.entity_id for e in res2.entities]
    assert res1.semantic_processing_fingerprint == res2.semantic_processing_fingerprint
