"""Tests for DocumentStateDTO compatibility and in-adapter conversion (P2A-R03)."""

import pytest
from langchain_core.documents import Document
from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.adapters.langgraph.exceptions import GraphStateValidationError
from md_generator.adapters.langgraph.nodes import create_context_builder_node, to_langchain_document
from md_generator.adapters.langgraph.state import DocumentStateDTO


def test_to_langchain_document_preserves_document_instance():
    """Passing a Document instance returns the instance without modification."""
    doc = Document(page_content="Text content", metadata={"tenant_id": "T1", "score": 0.9})
    converted = to_langchain_document(doc)
    assert converted is doc
    assert converted.page_content == "Text content"
    assert converted.metadata["tenant_id"] == "T1"


def test_to_langchain_document_converts_dto_dict():
    """Passing a DocumentStateDTO dictionary converts it into a valid Document instance."""
    dto: DocumentStateDTO = {
        "page_content": "DTO content",
        "metadata": {"tenant_id": "T1", "document_id": "doc-1", "score": 0.85},
    }
    converted = to_langchain_document(dto)
    assert hasattr(converted, "page_content")
    assert hasattr(converted, "metadata")
    assert converted.page_content == "DTO content"
    assert converted.metadata["tenant_id"] == "T1"
    assert converted.metadata["document_id"] == "doc-1"
    assert converted.metadata["score"] == 0.85


def test_to_langchain_document_rejects_unsupported_types():
    """Passing invalid objects raises GraphStateValidationError."""
    with pytest.raises(GraphStateValidationError, match="Cannot convert object of type 'int'"):
        to_langchain_document(123)

    with pytest.raises(GraphStateValidationError, match="Cannot convert object of type 'dict'"):
        to_langchain_document({"invalid_key": "val"})


def test_context_node_produces_identical_output_for_documents_and_dtos():
    """Equivalent Document instances and DocumentStateDTO dicts produce byte-for-byte identical serialized context."""
    builder = PromptContextBuilder(max_tokens=1000, include_citations=True)
    node = create_context_builder_node(builder, trusted_tenant="tenant-A")

    # Pure Document instances
    docs_input = [
        Document(
            page_content="System architecture overview.",
            metadata={"tenant_id": "tenant-A", "document_id": "arch-doc", "score": 0.95, "chunk_id": "c1"},
        ),
        Document(
            page_content="Database schema details.",
            metadata={"tenant_id": "tenant-A", "document_id": "db-doc", "score": 0.88, "chunk_id": "c2"},
        ),
    ]
    res_docs = node({"tenant_id": "tenant-A", "documents": docs_input})

    # Pure DTO dictionaries
    dtos_input = [
        {
            "page_content": "System architecture overview.",
            "metadata": {"tenant_id": "tenant-A", "document_id": "arch-doc", "score": 0.95, "chunk_id": "c1"},
        },
        {
            "page_content": "Database schema details.",
            "metadata": {"tenant_id": "tenant-A", "document_id": "db-doc", "score": 0.88, "chunk_id": "c2"},
        },
    ]
    res_dtos = node({"tenant_id": "tenant-A", "documents": dtos_input})

    assert res_docs["route"] == "synthesize"
    assert res_dtos["route"] == "synthesize"
    # Byte-for-byte identical serialized context output
    assert res_docs["context"] == res_dtos["context"]
    assert res_docs["context"].encode("utf-8") == res_dtos["context"].encode("utf-8")


def test_context_node_mixed_collection_document_and_dto():
    """Mixed collection (Document + DTO + Document + DTO) executes seamlessly and produces expected context."""
    builder = PromptContextBuilder(max_tokens=2000, include_citations=True)
    node = create_context_builder_node(builder, trusted_tenant="tenant-corp")

    mixed_input = [
        Document(
            page_content="Section 1",
            metadata={"tenant_id": "tenant-corp", "document_id": "d1", "score": 0.99, "chunk_id": "c1"},
        ),
        {
            "page_content": "Section 2",
            "metadata": {"tenant_id": "tenant-corp", "document_id": "d2", "score": 0.95, "chunk_id": "c2"},
        },
        Document(
            page_content="Section 3",
            metadata={"tenant_id": "tenant-corp", "document_id": "d3", "score": 0.90, "chunk_id": "c3"},
        ),
        {
            "page_content": "Section 4",
            "metadata": {"tenant_id": "tenant-corp", "document_id": "d4", "score": 0.85, "chunk_id": "c4"},
        },
    ]

    result = node({"tenant_id": "tenant-corp", "documents": mixed_input})
    assert result["route"] == "synthesize"
    context = result["context"]
    assert "Section 1" in context
    assert "Section 2" in context
    assert "Section 3" in context
    assert "Source: d1" in context
    assert "Source: d2" in context
    assert "Source: d3" in context
    assert "Source: d4" in context
