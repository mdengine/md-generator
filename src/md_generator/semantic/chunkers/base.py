"""Base dataclasses and Protocol interface for Phase 1A semantic chunkers.

Provides strict standard library types, diagnostics, parse status indicators,
and the BaseChunker protocol.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from md_generator.semantic.model.schema import Entity, Relationship, SemanticChunk, SemanticDocument, SourceLocation


class ParseStatus(str, Enum):
    """AST parse degradation status for ingestion documents."""
    CLEAN = "CLEAN"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"


@dataclass
class SemanticDiagnostic:
    """Diagnostic detail captured during AST parsing or semantic extraction."""
    severity: str                                       # 'INFO', 'WARNING', 'ERROR'
    code: str                                           # 'SYNTAX_ERROR', 'UNRESOLVED_REFERENCE', 'UNSUPPORTED_GRAMMAR'
    message: str
    source_location: Optional[SourceLocation] = None
    parser: str = "tree-sitter"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize diagnostic to a canonical JSON-compatible dictionary."""
        data: Dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "parser": self.parser,
        }
        if self.source_location is not None:
            data["source_location"] = self.source_location.to_dict()
        return data


@dataclass
class SymbolExtractionResult:
    """Container for entities, relationships, diagnostics, and parse status resulting from AST extraction."""
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    diagnostics: List[SemanticDiagnostic] = field(default_factory=list)
    parse_status: ParseStatus = ParseStatus.CLEAN


class BaseChunker(Protocol):
    """Protocol interface implemented by all Phase 1A structural domain chunkers."""

    def supports(self, source_type: str) -> bool:
        """Return True if this chunker handles the given source_type or language."""
        ...

    def chunk_document(
        self, document: SemanticDocument
    ) -> List[SemanticChunk]:
        """Parse SemanticDocument into structural SemanticChunks."""
        ...

    def extract_symbols(
        self, document: SemanticDocument
    ) -> SymbolExtractionResult:
        """Extract domain Entities, Relationships, and Diagnostics from document AST."""
        ...
