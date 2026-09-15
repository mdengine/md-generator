"""Contract Test Suite for Phase 0A Canonical Data Models.

Verifies schema versioning, __post_init__ validation, 64-char SHA-256 hex IDs,
SourceLocation domain rules, unknown field rejection, recursive nested validation,
and deterministic lossless round-trip serialization.
"""

import json
import pytest
from md_generator.semantic.model import (
    SCHEMA_VERSION,
    InvalidSchemaError,
    SourceLocation,
    Entity,
    Relationship,
    CanonicalMetadata,
    DocumentLineage,
    ChunkLineage,
    SecurityMetadata,
    SemanticDocument,
    SemanticChunk,
)

# Standard 64-character SHA-256 test hex strings
SAMPLE_SHA256_DOC_ID = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
SAMPLE_SHA256_CHUNK_ID = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
SAMPLE_HEX_ENTITY_ID = "e101"
SAMPLE_HEX_REL_ID = "f101"


def test_schema_version_freeze():
    assert SCHEMA_VERSION == "1.0"


def test_source_location_validation():
    # Common fields (location_type, uri, path) valid for any domain
    loc_common = SourceLocation(location_type="pdf", uri="file:///doc.pdf", path="/doc.pdf", page=12)
    assert loc_common.location_type == "pdf"
    assert loc_common.page == 12

    # Domain field valid for code
    loc_code = SourceLocation(
        location_type="code",
        uri="file:///src/main.py",
        path="src/main.py",
        line_start=10,
        line_end=25,
        symbol="main_function",
    )
    assert loc_code.line_start == 10

    # Domain mismatch: specifying 'page' (PDF) on a 'code' location_type must raise InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="Field 'page' is not permitted for location_type 'code'"):
        SourceLocation(location_type="code", line_start=10, page=5)

    # Invalid location_type raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="Invalid location_type"):
        SourceLocation(location_type="unsupported_domain")


def test_entity_validation():
    loc = SourceLocation(location_type="code", uri="file:///app.py", path="app.py", symbol="UserClass")
    entity = Entity(
        entity_id=SAMPLE_HEX_ENTITY_ID,
        entity_type="class",
        name="UserClass",
        qualified_name="auth.models.UserClass",
        location=loc,
    )
    assert entity.name == "UserClass"

    # Non-hex entity_id raises InvalidSchemaError immediately upon instantiation
    with pytest.raises(InvalidSchemaError, match="Entity.entity_id must be a valid hexadecimal string"):
        Entity(entity_id="invalid-non-hex!", entity_type="class", name="Foo", qualified_name="Foo")

    # Empty name raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="Entity.name must be a non-empty string"):
        Entity(entity_id="a1b2", entity_type="class", name="", qualified_name="Foo")


def test_relationship_validation():
    rel = Relationship(
        relationship_id=SAMPLE_HEX_REL_ID,
        source_entity_id="e101",
        target_entity_id="e102",
        relationship_type="CALLS",
        confidence=0.95,
    )
    assert rel.confidence == 0.95

    # Out of range confidence raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="Relationship.confidence must be a float between 0.0 and 1.0"):
        Relationship(
            relationship_id="f101",
            source_entity_id="e101",
            target_entity_id="e102",
            relationship_type="CALLS",
            confidence=1.5,
        )


def test_canonical_metadata_validation():
    meta = CanonicalMetadata(
        system="ERP",
        domain="finance",
        module="billing",
        source_type="sap",
        repository="org/repo",
    )
    assert meta.system == "ERP"
    assert meta.repository == "org/repo"


def test_lineage_and_security_validation():
    doc_lineage = DocumentLineage(source_hash="sha256_hash", extractor_name="treesitter")
    assert doc_lineage.extractor_name == "treesitter"

    chunk_lineage = ChunkLineage(source_hash="sha256_hash", chunk_hash="chunk_sha", sequence_index=0)
    assert chunk_lineage.sequence_index == 0

    sec = SecurityMetadata(is_sanitized=True, secrets_redacted_count=2)
    assert sec.secrets_redacted_count == 2


def test_semantic_document_validation():
    doc = SemanticDocument(
        document_id=SAMPLE_SHA256_DOC_ID,
        sanitized_content="sanitized source text",
        document_type="code",
    )
    assert doc.document_id == SAMPLE_SHA256_DOC_ID

    # Non-64-char or non-hex document_id raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="SemanticDocument.document_id must be a valid 64-character hex SHA-256 string"):
        SemanticDocument(document_id="short_id_12345", sanitized_content="test")

    # Unsupported schema_version raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="Unsupported schema_version"):
        SemanticDocument(schema_version="0.9", document_id=SAMPLE_SHA256_DOC_ID)


def test_semantic_chunk_validation():
    chunk = SemanticChunk(
        chunk_id=SAMPLE_SHA256_CHUNK_ID,
        document_id=SAMPLE_SHA256_DOC_ID,
        sanitized_content="function chunk code",
    )
    assert chunk.chunk_id == SAMPLE_SHA256_CHUNK_ID
    assert chunk.document_id == SAMPLE_SHA256_DOC_ID

    # Invalid hex chunk_id raises InvalidSchemaError
    with pytest.raises(InvalidSchemaError, match="SemanticChunk.chunk_id must be a valid 64-character hex SHA-256 string"):
        SemanticChunk(chunk_id="invalid-id", document_id=SAMPLE_SHA256_DOC_ID)


def test_unknown_field_rejection():
    data = {
        "schema_version": "1.0",
        "document_id": SAMPLE_SHA256_DOC_ID,
        "sanitized_content": "test",
        "unknown_extra_field": "disallowed",
    }
    with pytest.raises(InvalidSchemaError, match=r"Unknown fields for SemanticDocument: \['unknown_extra_field'\]"):
        SemanticDocument.from_dict(data)


def test_recursive_nested_validation():
    # Invalid nested entity inside SemanticDocument from_dict raises InvalidSchemaError
    invalid_entity_dict = {
        "entity_id": "not-valid-hex!",
        "entity_type": "class",
        "name": "Foo",
        "qualified_name": "Foo",
    }
    data = {
        "schema_version": "1.0",
        "document_id": SAMPLE_SHA256_DOC_ID,
        "sanitized_content": "code",
        "entities": [invalid_entity_dict],
    }
    with pytest.raises(InvalidSchemaError, match="Entity.entity_id must be a valid hexadecimal string"):
        SemanticDocument.from_dict(data)


def test_deterministic_json_serialization():
    meta = CanonicalMetadata(domain="test", system="sys")
    doc = SemanticDocument(
        document_id=SAMPLE_SHA256_DOC_ID,
        sanitized_content="hello",
        metadata=meta,
    )
    json_str = doc.to_json()
    assert json_str.startswith('{"document_id":"')
    assert '"schema_version":"1.0"' in json_str
    # Verify deterministic sort_keys & compact separators
    assert ' , ' not in json_str
    assert ' : ' not in json_str


def test_lossless_roundtrip_serialization():
    loc = SourceLocation(location_type="code", uri="file:///main.py", path="main.py", line_start=1, line_end=50)
    entity = Entity(entity_id="e1001", entity_type="function", name="main", qualified_name="app.main", location=loc)
    rel = Relationship(relationship_id="f1001", source_entity_id="e1001", target_entity_id="e1002", relationship_type="CALLS")
    meta = CanonicalMetadata(system="app", domain="core", language="python")
    lineage = DocumentLineage(source_hash="hash123", extractor_name="treesitter")
    sec = SecurityMetadata(is_sanitized=True, secrets_redacted_count=1)

    doc = SemanticDocument(
        schema_version="1.0",
        document_id=SAMPLE_SHA256_DOC_ID,
        sanitized_content="def main(): pass",
        document_type="code",
        metadata=meta,
        entities=[entity],
        relationships=[rel],
        lineage=lineage,
        security=sec,
    )

    # dict roundtrip
    dict_data = doc.to_dict()
    doc_reconstructed = SemanticDocument.from_dict(dict_data)
    assert doc_reconstructed.to_dict() == dict_data

    # json roundtrip
    json_str = doc.to_json()
    doc_from_json = SemanticDocument.from_json(json_str)
    assert doc_from_json.to_json() == json_str
    assert doc_from_json.entities[0].location.line_start == 1


def test_base_import_isolation():
    import md_generator
    from md_generator.semantic.model import SCHEMA_VERSION, SemanticDocument
    assert md_generator.__version__ == "0.13.4"
    assert SCHEMA_VERSION == "1.0"
