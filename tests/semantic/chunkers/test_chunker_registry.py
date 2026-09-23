"""Tests for ChunkerRegistry resolution dispatch and AmbiguousChunkerError handling."""

import pytest
from md_generator.semantic.chunkers.base import BaseChunker, SymbolExtractionResult
from md_generator.semantic.chunkers.registry import AmbiguousChunkerError, ChunkerRegistry
from md_generator.semantic.chunkers.code import CodeChunker
from md_generator.semantic.chunkers.openapi import OpenAPIChunker
from md_generator.semantic.chunkers.sap import SAPChunker
from md_generator.semantic.chunkers.db import DBChunker
from md_generator.semantic.model.schema import SemanticChunk, SemanticDocument


class CustomChunker:
    def supports(self, source_type: str) -> bool:
        return source_type == "custom"

    def chunk_document(self, document: SemanticDocument) -> list[SemanticChunk]:
        return []

    def extract_symbols(self, document: SemanticDocument) -> SymbolExtractionResult:
        return SymbolExtractionResult()


def test_registry_default_population():
    registry = ChunkerRegistry.get_default()
    assert isinstance(registry.resolve("py"), CodeChunker)
    assert isinstance(registry.resolve("openapi"), OpenAPIChunker)
    assert isinstance(registry.resolve("abap"), SAPChunker)
    assert isinstance(registry.resolve("sql"), DBChunker)


def test_registry_explicit_source_type_precedence():
    registry = ChunkerRegistry()
    custom = CustomChunker()
    registry.register(custom, explicit_source_type="python")
    # Explicit binding overrides standard supports check
    resolved = registry.resolve("python")
    assert resolved is custom


def test_ambiguous_registration_raises_error():
    registry = ChunkerRegistry()
    c1 = CustomChunker()
    c2 = CustomChunker()
    registry.register(c1, explicit_source_type="custom")
    with pytest.raises(AmbiguousChunkerError):
        registry.register(c2, explicit_source_type="custom")


def test_unsupported_source_returns_none():
    registry = ChunkerRegistry()
    assert registry.resolve("unknown_format") is None
    assert registry.resolve("") is None
