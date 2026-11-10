"""Tests for Tree-sitter ERROR node parse degradation and ParseStatus reporting."""

import hashlib
from md_generator.semantic.chunkers.code import CodeChunker
from md_generator.semantic.chunkers.base import ParseStatus
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_syntax_error_parse_recovery():
    chunker = CodeChunker()
    broken_code = """class ValidClass:
    def valid_method(self):
        pass

def broken_func(
    incomplete_syntax...
"""

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-diag-1"),
        sanitized_content=broken_code,
        metadata=CanonicalMetadata(source_uri="file:///broken.py", source_type="py", language="python"),
    )

    res = chunker.extract_symbols(doc)
    assert res.parse_status in (ParseStatus.RECOVERED, ParseStatus.FAILED)
    class_entities = [e for e in res.entities if "ValidClass" in e.name]
    assert len(class_entities) >= 1
    assert any(d.code == "SYNTAX_ERROR" for d in res.diagnostics)
