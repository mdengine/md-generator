"""Tests for Tree-sitter CodeChunker AST parsing and symbol extraction."""

import hashlib
from md_generator.semantic.chunkers.code import CodeChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_python_code_chunking():
    chunker = CodeChunker()
    code = """def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""
    doc = SemanticDocument(
        document_id=_make_doc_id("doc-py-1"),
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///test.py", source_type="py", language="python"),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 2
    symbols = [c.metadata.symbol_name for c in chunks if c.metadata]
    assert any("add" in s for s in symbols if s)
    assert any("Calculator" in s for s in symbols if s)


def test_java_code_chunking():
    chunker = CodeChunker()
    code = """package com.example;

public class PaymentService {
    public void processPayment() {
        validate();
    }
}
"""
    doc = SemanticDocument(
        document_id=_make_doc_id("doc-java-1"),
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///PaymentService.java", source_type="java", language="java"),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 1
    symbols = [c.metadata.symbol_name for c in chunks if c.metadata]
    assert any("PaymentService" in s for s in symbols if s)


def test_code_symbol_extraction():
    chunker = CodeChunker()
    code = """class Service:
    def execute(self):
        pass
"""
    doc = SemanticDocument(
        document_id=_make_doc_id("doc-py-2"),
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///service.py", source_type="py", language="python"),
    )

    res = chunker.extract_symbols(doc)
    assert len(res.entities) >= 1
    types = [e.entity_type for e in res.entities]
    assert "CLASS" in types or "FUNCTION" in types or "METHOD" in types
