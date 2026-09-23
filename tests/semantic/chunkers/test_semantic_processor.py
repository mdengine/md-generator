"""Tests for SemanticProcessor composition layer."""

import hashlib
from md_generator.pipeline.result import IngestionResult
from md_generator.semantic.processor import SemanticProcessor
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_semantic_processor_composition_end_to_end():
    processor = SemanticProcessor()

    py_doc = SemanticDocument(
        document_id=_make_doc_id("doc-proc-1"),
        sanitized_content="def main():\n    print('Hello World')\n",
        metadata=CanonicalMetadata(source_uri="file:///main.py", source_type="py", language="python"),
    )

    sql_doc = SemanticDocument(
        document_id=_make_doc_id("doc-proc-2"),
        sanitized_content="CREATE TABLE products (id INT PRIMARY KEY);",
        metadata=CanonicalMetadata(source_uri="file:///schema.sql", source_type="sql"),
    )

    ingestion_result = IngestionResult(
        run_id="run-test-123",
        documents=[py_doc, sql_doc],
        execution_fingerprint="exec-fp-123",
    )

    res = processor.process_result(ingestion_result)
    assert len(res.chunks) >= 2
    assert len(res.entities) >= 2
    assert len(res.semantic_processing_fingerprint) == 64

    d = res.to_dict()
    assert "chunks" in d
    assert "entities" in d
    assert "semantic_processing_fingerprint" in d
