"""Non-breaking Phase 1A SemanticProcessor composition layer.

Ingests Phase 0C IngestionResult or List[SemanticDocument] and executes
structural chunking and symbol extraction without modifying Phase 0C pipeline code.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional

from md_generator.pipeline.result import IngestionResult
from md_generator.semantic.chunkers.base import BaseChunker, SemanticDiagnostic, SymbolExtractionResult
from md_generator.semantic.chunkers.registry import ChunkerRegistry
from md_generator.semantic.model.schema import Entity, Relationship, SemanticChunk, SemanticDocument


@dataclass
class SemanticProcessingResult:
    """Result of Phase 1A semantic processing on ingested documents."""
    chunks: List[SemanticChunk] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    diagnostics: List[SemanticDiagnostic] = field(default_factory=list)
    semantic_processing_fingerprint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to a canonical JSON-compatible dictionary."""
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "semantic_processing_fingerprint": self.semantic_processing_fingerprint,
        }


class SemanticProcessor:
    """Composition layer orchestrating Phase 1A chunking and symbol extraction."""

    def __init__(self, registry: Optional[ChunkerRegistry] = None):
        self.chunker_registry = registry or ChunkerRegistry.get_default()

    def process_result(self, ingestion_result: IngestionResult) -> SemanticProcessingResult:
        """Process Phase 0C IngestionResult."""
        return self.process_documents(ingestion_result.documents)

    def process_documents(self, documents: List[SemanticDocument]) -> SemanticProcessingResult:
        """Process a list of SemanticDocuments into structural chunks, entities, relationships, and diagnostics."""
        chunks = self._chunking_stage(documents)
        extraction = self._semantic_extraction_stage(documents)
        fingerprint = self._compute_semantic_processing_fingerprint(documents, chunks)

        return SemanticProcessingResult(
            chunks=chunks,
            entities=extraction.entities,
            relationships=extraction.relationships,
            diagnostics=extraction.diagnostics,
            semantic_processing_fingerprint=fingerprint,
        )

    def _chunking_stage(self, documents: List[SemanticDocument]) -> List[SemanticChunk]:
        all_chunks: List[SemanticChunk] = []
        for doc in documents:
            st = doc.metadata.source_type if doc.metadata and doc.metadata.source_type else "generic"
            chunker = self.chunker_registry.resolve(st)
            if chunker:
                doc_chunks = chunker.chunk_document(doc)
                all_chunks.extend(doc_chunks)
        return all_chunks

    def _semantic_extraction_stage(
        self, documents: List[SemanticDocument]
    ) -> SymbolExtractionResult:
        all_entities: List[Entity] = []
        all_relationships: List[Relationship] = []
        all_diagnostics: List[SemanticDiagnostic] = []

        for doc in documents:
            st = doc.metadata.source_type if doc.metadata and doc.metadata.source_type else "generic"
            chunker = self.chunker_registry.resolve(st)
            if chunker:
                res = chunker.extract_symbols(doc)
                all_entities.extend(res.entities)
                all_relationships.extend(res.relationships)
                all_diagnostics.extend(res.diagnostics)

        return SymbolExtractionResult(
            entities=all_entities,
            relationships=all_relationships,
            diagnostics=all_diagnostics,
        )

    def _compute_semantic_processing_fingerprint(
        self, documents: List[SemanticDocument], chunks: List[SemanticChunk]
    ) -> str:
        fingerprint_data = {
            "chunker_version": "1.0",
            "document_ids": sorted([doc.document_id for doc in documents if doc.document_id]),
            "chunk_ids": sorted([c.chunk_id for c in chunks if c.chunk_id]),
        }
        raw_bytes = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()
