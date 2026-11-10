"""Tests for syntactic call graph and unresolved reference extraction."""

import hashlib
from md_generator.semantic.chunkers.code import CodeChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_syntactic_call_graph_and_unresolved_references():
    chunker = CodeChunker()
    code = """class OrderService:
    def process(self):
        self.validate()
        externalService.doSomething()

    def validate(self):
        pass
"""

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-rel-1"),
        sanitized_content=code,
        metadata=CanonicalMetadata(source_uri="file:///orders.py", source_type="py", language="python"),
    )

    res = chunker.extract_symbols(doc)
    calls = [r for r in res.relationships if r.relationship_type == "CALLS"]
    assert len(calls) >= 1
    unresolved_targets = [r for r in calls if r.provenance.get("resolution_status") == "unresolved"]
    assert len(unresolved_targets) >= 1
