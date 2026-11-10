import hashlib
import pytest

from md_generator.graph.exceptions import TenantBoundaryError, GraphError
from md_generator.graph.extractor import extract
from md_generator.semantic.model.schema import (
    SemanticDocument,
    SemanticChunk,
    Entity,
    Relationship,
    SourceLocation,
    ChunkLineage,
)


def test_extractor_mandatory_tenant():
    doc_id = hashlib.sha256(b"doc-1").hexdigest()
    doc = SemanticDocument(document_id=doc_id, sanitized_content="test")
    chunks = []
    with pytest.raises(TenantBoundaryError):
        extract(doc, chunks, tenant_id="")
    with pytest.raises(TenantBoundaryError):
        extract(doc, chunks, tenant_id="   ")


def test_extractor_option_a_dedup_and_property_conflict():
    doc_id = hashlib.sha256(b"doc-1").hexdigest()
    chunk_id = hashlib.sha256(b"chunk-1").hexdigest()

    loc = SourceLocation(location_type="code", path="test.py", line_start=1, line_end=10)
    ent_id = hashlib.sha256(b"func_main").hexdigest()
    ent_doc = Entity(
        entity_id=ent_id,
        entity_type="function",
        name="main",
        qualified_name="pkg.main",
        location=loc,
        metadata={"author": "alice", "doc_field": "val1", "tags": ["core"]},
    )
    ent_chunk = Entity(
        entity_id=ent_id,
        entity_type="function",
        name="main",
        qualified_name="pkg.main",
        location=loc,
        metadata={"author": "bob", "chunk_field": "val2", "tags": ["runtime"]},  # author conflicts: chunk > doc
    )

    doc = SemanticDocument(
        document_id=doc_id,
        sanitized_content="hello world",
        entities=[ent_doc],
        relationships=[],
    )
    chunk = SemanticChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        sanitized_content="hello",
        lineage=ChunkLineage(location=loc),
        entities=[ent_chunk],
        relationships=[],
    )

    kg = extract(doc, [chunk], tenant_id="tenant-prod")

    assert kg.tenant_id == "tenant-prod"
    # Find entity node
    ent_node = None
    for n in kg.nodes.values():
        if n.entity_id == ent_id:
            ent_node = n
            break

    assert ent_node is not None
    # Property conflict check: chunk author "bob" overrides doc "alice"
    assert ent_node.properties["author"] == "bob"
    assert ent_node.properties["doc_field"] == "val1"
    assert ent_node.properties["chunk_field"] == "val2"
    # List union check
    assert sorted(ent_node.properties["tags"]) == ["core", "runtime"]
    # Document IDs and Chunk IDs check
    assert doc_id in ent_node.document_ids
    assert chunk_id in ent_node.chunk_ids


def test_structural_nodes_and_edges():
    doc_id = hashlib.sha256(b"doc-1").hexdigest()
    chunk_id = hashlib.sha256(b"chunk-1").hexdigest()

    doc = SemanticDocument(document_id=doc_id, sanitized_content="content")
    chunk = SemanticChunk(chunk_id=chunk_id, document_id=doc_id, sanitized_content="c1")

    kg = extract(doc, [chunk], tenant_id="tenant-prod")

    doc_node = next(n for n in kg.nodes.values() if n.entity_type == "document")
    chunk_node = next(n for n in kg.nodes.values() if n.entity_type == "chunk")

    assert doc_node.entity_id == doc_id
    assert chunk_node.entity_id == chunk_id

    # CONTAINS_CHUNK edge
    contains_chunk = next(e for e in kg.edges.values() if e.relationship_type == "CONTAINS_CHUNK")
    assert contains_chunk.source_id == doc_node.node_id
    assert contains_chunk.target_id == chunk_node.node_id


def test_extractor_source_immutability():
    doc_id = hashlib.sha256(b"doc-immutable").hexdigest()
    chunk_id = hashlib.sha256(b"chunk-immutable").hexdigest()
    ent_id = hashlib.sha256(b"ent-immutable").hexdigest()

    ent = Entity(
        entity_id=ent_id,
        entity_type="class",
        name="Cls",
        qualified_name="pkg.Cls",
        metadata={"key": "val"},
    )
    doc = SemanticDocument(
        document_id=doc_id,
        sanitized_content="content",
        entities=[ent],
    )
    chunk = SemanticChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        sanitized_content="chunk content",
    )

    doc_before = doc.to_dict()
    chunk_before = chunk.to_dict()

    extract(doc, [chunk], tenant_id="tenant-immut")

    assert doc.to_dict() == doc_before
    assert chunk.to_dict() == chunk_before


def test_extractor_relationship_extraction_and_sanitization():
    doc_id = hashlib.sha256(b"doc-rel").hexdigest()
    ent1_id = hashlib.sha256(b"ent-1").hexdigest()
    ent2_id = hashlib.sha256(b"ent-2").hexdigest()

    rel = Relationship(
        relationship_id=hashlib.sha256(b"rel-1").hexdigest(),
        source_entity_id=ent1_id,
        target_entity_id=ent2_id,
        relationship_type="calls-async",
        confidence=0.88,
        provenance={"channel": "static_analysis"},
    )
    doc = SemanticDocument(
        document_id=doc_id,
        sanitized_content="doc content",
        relationships=[rel],
    )

    kg = extract(doc, [], tenant_id="tenant-rel")
    assert len(kg.edges) > 0
    edge = next(e for e in kg.edges.values() if e.source_id.endswith(ent1_id))
    # Sanitized relationship type
    assert edge.relationship_type == "CALLS_ASYNC"
    assert edge.weight == 0.88
    assert edge.properties["channel"] == "static_analysis"
