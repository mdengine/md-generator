"""Tests for source location precision and line/col precision."""

import hashlib
from md_generator.semantic.chunkers.code import CodeChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_source_location_line_col_precision():
    chunker = CodeChunker()
    code = "def hello():\n    pass\n"
    doc = SemanticDocument(
        document_id=_make_doc_id("doc-loc-1"),
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///hello.py", source_type="py", language="python"),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 1
    chunk = chunks[0]
    lineage = chunk.lineage
    assert lineage is not None
    assert lineage.location is not None
    assert lineage.location.uri == "file:///hello.py"
    assert lineage.location.line_start >= 1
