"""Tests for MDDocumentLoader adapter component."""

import copy
import pytest
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from md_generator.semantic.model.schema import (
    SemanticDocument,
    SemanticChunk,
    CanonicalMetadata,
    SourceLocation,
    ChunkLineage,
    Entity,
)
from md_generator.vector.exceptions import TenantBoundaryError
from md_generator.adapters.langchain.loader import (
    MDDocumentLoader,
    extract_semantic_key,
    resolve_tenant_id,
)


def _sample_doc_id() -> str:
    return "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"


def _sample_chunk_id(suffix: str = "1") -> str:
    return f"c1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b{suffix}"


def test_loader_subclasses_base_loader():
    """Validates that MDDocumentLoader subclasses LangChain's BaseLoader."""
    assert issubclass(MDDocumentLoader, BaseLoader)


def test_loader_inherited_load():
    """Validates that MDDocumentLoader does not override load() and inherits BaseLoader.load()."""
    assert type(MDDocumentLoader.load) is not None
    # Confirm load is inherited from BaseLoader
    assert MDDocumentLoader.load == BaseLoader.load


def test_loader_lazy_load_interface():
    """Validates that lazy_load() returns an iterator of LangChain Document objects."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="def hello(): pass",
    )
    loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-alpha")
    gen = loader.lazy_load()
    assert hasattr(gen, "__iter__")
    assert hasattr(gen, "__next__")

    docs = list(gen)
    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].page_content == "def hello(): pass"
    assert docs[0].metadata["tenant_id"] == "tenant-alpha"
    assert docs[0].metadata["chunk_id"] == chunk.chunk_id
    assert docs[0].metadata["document_id"] == chunk.document_id


def test_loader_inherited_load_execution():
    """Validates that inherited load() method collects lazy_load() output."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="SELECT * FROM table",
    )
    loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-alpha")
    docs = loader.load()
    assert isinstance(docs, list)
    assert len(docs) == 1
    assert docs[0].page_content == "SELECT * FROM table"


def test_loader_non_mutating():
    """Validates that input models are never mutated during conversion."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="const x = 1;",
        metadata=CanonicalMetadata(
            system="generic",
            security_classification="confidential",
        ),
        lineage=ChunkLineage(
            parent_chunk_id="b1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            location=SourceLocation(location_type="code", path="src/index.ts", line_start=1, line_end=5),
        ),
    )
    chunk_copy = copy.deepcopy(chunk)
    loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-alpha")
    _ = loader.load()

    assert chunk == chunk_copy


def test_loader_document_page_content():
    """Validates conversion of a full SemanticDocument."""
    doc = SemanticDocument(
        document_id=_sample_doc_id(),
        sanitized_content="# Readme content",
        metadata=CanonicalMetadata(
            system="sap",
            security_classification="internal",
            source_path="docs/README.md",
        ),
    )
    loader = MDDocumentLoader(semantic_document=doc, tenant_id="tenant-alpha")
    docs = loader.load()
    assert len(docs) == 1
    assert docs[0].page_content == "# Readme content"
    assert docs[0].metadata["document_id"] == _sample_doc_id()
    assert docs[0].metadata["chunk_id"] is None
    assert docs[0].metadata["tenant_id"] == "tenant-alpha"
    assert docs[0].metadata["security_classification"] == "internal"


def test_loader_chunk_page_content_multi():
    """Validates conversion of multiple SemanticChunk instances."""
    chunks = [
        SemanticChunk(
            chunk_id=_sample_chunk_id(str(i)),
            document_id=_sample_doc_id(),
            sanitized_content=f"chunk content {i}",
        )
        for i in range(3)
    ]
    loader = MDDocumentLoader(chunks=chunks, tenant_id="tenant-alpha")
    docs = loader.load()
    assert len(docs) == 3
    for i, doc in enumerate(docs):
        assert doc.page_content == f"chunk content {i}"
        assert doc.metadata["chunk_id"] == _sample_chunk_id(str(i))


def test_loader_rejects_missing_tenant_even_with_system_metadata():
    """Validates that metadata.system ('sap_erp') is never inferred as tenant_id and raises TenantBoundaryError."""
    doc = SemanticDocument(
        document_id=_sample_doc_id(),
        sanitized_content="platform content",
        metadata=CanonicalMetadata(
            system="sap_erp",
        ),
    )
    loader = MDDocumentLoader(semantic_document=doc)  # No explicit tenant_id
    with pytest.raises(TenantBoundaryError, match="Cannot load document without tenant identity"):
        _ = loader.load()


def test_loader_rejects_conflicting_tenant():
    """Validates that explicit tenant_id conflicting with model.tenant_id raises TenantBoundaryError."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="conflicting tenant chunk",
    )
    # Simulate chunk with tenant_id attribute
    chunk.tenant_id = "tenant-A"

    loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-B")
    with pytest.raises(TenantBoundaryError, match="Conflicting tenant identity"):
        _ = loader.load()


def test_loader_model_tenant_success():
    """Validates model tenant_id is used when loader explicit tenant is not provided."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="chunk with model tenant",
    )
    chunk.tenant_id = "tenant-from-model"

    loader = MDDocumentLoader(chunks=[chunk])
    docs = loader.load()
    assert len(docs) == 1
    assert docs[0].metadata["tenant_id"] == "tenant-from-model"


def test_loader_canonical_semantic_key():
    """Validates canonical semantic_key extraction from entity or metadata."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="entity chunk",
        entities=[
            Entity(
                entity_id="e1b2c3d4e5f6",
                entity_type="function",
                name="my_func",
                qualified_name="custom.package.my_func",
                metadata={"semantic_key": "custom.package.my_func"},
            )
        ],
    )
    loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-alpha")
    docs = loader.load()
    assert docs[0].metadata["semantic_key"] == "custom.package.my_func"


def test_loader_metadata_boundary():
    """Validates that Document.metadata contains canonical fields and zero credentials or secrets."""
    chunk = SemanticChunk(
        chunk_id=_sample_chunk_id(),
        document_id=_sample_doc_id(),
        sanitized_content="clean content",
    )
    loader = MDDocumentLoader(chunks=[chunk], tenant_id="tenant-alpha")
    docs = loader.load()
    meta = docs[0].metadata
    # Required keys
    assert "document_id" in meta
    assert "chunk_id" in meta
    assert "tenant_id" in meta
    assert "semantic_key" in meta
    assert "security_classification" in meta
    # No credentials
    for secret_key in ["password", "secret", "api_key", "token", "credentials"]:
        assert secret_key not in meta


def test_loader_validation_errors():
    """Validates input validation on MDDocumentLoader construction."""
    with pytest.raises(ValueError, match="requires either a semantic_document or non-empty chunks list"):
        MDDocumentLoader()

    with pytest.raises(TenantBoundaryError, match="must be a non-empty string"):
        MDDocumentLoader(
            chunks=[SemanticChunk(chunk_id=_sample_chunk_id(), document_id=_sample_doc_id(), sanitized_content="x")],
            tenant_id="   ",
        )
