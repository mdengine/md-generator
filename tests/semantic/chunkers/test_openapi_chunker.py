"""Tests for OpenAPI domain chunker."""

import hashlib
import json
from md_generator.semantic.chunkers.openapi import OpenAPIChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_openapi_endpoint_chunking():
    chunker = OpenAPIChunker()
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Payment API", "version": "1.0"},
        "paths": {
            "/v1/payments": {
                "post": {"summary": "Process payment", "responses": {"200": {"description": "OK"}}},
                "get": {"summary": "Get payment status", "responses": {"200": {"description": "OK"}}},
            }
        },
    }

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-openapi-1"),
        sanitized_content=json.dumps(spec),
        metadata=CanonicalMetadata(source_uri="file:///openapi.json", source_type="openapi"),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 2
    paths = [c.metadata.api_path for c in chunks if c.metadata]
    assert "/v1/payments" in paths


def test_openapi_symbol_extraction():
    chunker = OpenAPIChunker()
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/v1/orders": {
                "post": {"summary": "Create order"}
            }
        },
    }

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-openapi-2"),
        sanitized_content=json.dumps(spec),
        metadata=CanonicalMetadata(source_uri="file:///openapi.json", source_type="openapi"),
    )

    res = chunker.extract_symbols(doc)
    assert len(res.entities) == 1
    assert res.entities[0].entity_type == "ENDPOINT"
    assert res.entities[0].name == "POST /v1/orders"
