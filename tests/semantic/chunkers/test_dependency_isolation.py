"""Tests for Tree-sitter import isolation and standard library core compatibility."""

import hashlib
from md_generator.semantic.chunkers.code import CodeChunker, _get_tree_sitter_language
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_dependency_isolation_absent_grammar():
    lang_obj, capability = _get_tree_sitter_language("nonexistent_language_123")
    assert lang_obj is None
    assert capability is None


def test_fallback_when_tree_sitter_unavailable(monkeypatch):
    chunker = CodeChunker()
    doc = SemanticDocument(
        document_id=_make_doc_id("doc-iso-1"),
        sanitized_content="x = 42\n",
        metadata=CanonicalMetadata(source_uri="file:///test.py", source_type="py", language="python"),
    )

    monkeypatch.setattr("md_generator.semantic.chunkers.code._TREE_SITTER_AVAILABLE", False)
    monkeypatch.setattr("md_generator.semantic.chunkers.code.tree_sitter", None)

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].sanitized_content == "x = 42\n"

    res = chunker.extract_symbols(doc)
    assert res.parse_status.value == "FAILED"
    assert any(d.code == "UNSUPPORTED_GRAMMAR" for d in res.diagnostics)
