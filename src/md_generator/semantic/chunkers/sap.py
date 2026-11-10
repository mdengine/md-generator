"""SAP ABAP function module and IDoc domain chunker."""

import hashlib
import re
from typing import List
from md_generator.lineage.ids import generate_chunk_id
from md_generator.semantic.chunkers.base import SymbolExtractionResult, ParseStatus
from md_generator.semantic.chunkers.identity import EntityType, compute_fqn
from md_generator.semantic.model.schema import (
    CanonicalMetadata,
    ChunkLineage,
    Entity,
    SemanticChunk,
    SemanticDocument,
    SourceLocation,
)


class SAPChunker:
    """Domain chunker for SAP ABAP function modules, classes, and IDocs."""

    def __init__(self, chunker_version: str = "1.0"):
        self.chunker_version = chunker_version

    def supports(self, source_type: str) -> bool:
        st = source_type.strip().lower()
        return "sap" in st or "abap" in st or "idoc" in st or st.endswith(".abap")

    def chunk_document(self, document: SemanticDocument) -> List[SemanticChunk]:
        content = document.sanitized_content
        doc_id = document.document_id
        chunks: List[SemanticChunk] = []

        fn_matches = re.finditer(
            r"FUNCTION\s+([A-Z0-9_]+)\.(.*?)ENDFUNCTION",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        for match in fn_matches:
            fn_name = match.group(1).upper()
            fn_body = match.group(0)
            identity = compute_fqn("sap", "sap_object", f"FUNCTION_MODULE:{fn_name}")
            sem_key = identity.compute_semantic_key()
            content_hash = hashlib.sha256(fn_body.encode("utf-8")).hexdigest()
            chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)

            uri = document.metadata.source_uri if document.metadata else ""
            loc = SourceLocation(
                location_type="sap",
                uri=uri,
                sap_object=fn_name,
            )
            lineage = ChunkLineage(
                source_hash=content_hash,
                chunk_hash=content_hash,
                sequence_index=len(chunks),
                location=loc,
            )

            chunk_metadata = None
            if document.metadata:
                chunk_metadata = CanonicalMetadata(
                    system=document.metadata.system,
                    domain=document.metadata.domain,
                    module=document.metadata.module,
                    source_type="sap",
                    source_uri=document.metadata.source_uri,
                    symbol_name=fn_name,
                )

            chunks.append(
                SemanticChunk(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    sanitized_content=fn_body,
                    metadata=chunk_metadata,
                    lineage=lineage,
                )
            )

        if not chunks:
            return self._fallback_single_chunk(document)

        return chunks

    def extract_symbols(self, document: SemanticDocument) -> SymbolExtractionResult:
        content = document.sanitized_content
        doc_id = document.document_id
        entities: List[Entity] = []

        fn_matches = re.finditer(r"FUNCTION\s+([A-Z0-9_]+)\.", content, re.IGNORECASE)
        for match in fn_matches:
            fn_name = match.group(1).upper()
            sem_key = f"sap_object:FUNCTION_MODULE:{fn_name}"
            entity_id = hashlib.sha256(f"{doc_id}:{sem_key}".encode("utf-8")).hexdigest()

            uri = document.metadata.source_uri if document.metadata else ""
            loc = SourceLocation(
                location_type="sap",
                uri=uri,
                sap_object=fn_name,
            )

            entities.append(
                Entity(
                    entity_id=entity_id,
                    entity_type=EntityType.SAP_OBJECT.value,
                    name=fn_name,
                    qualified_name=f"FUNCTION_MODULE:{fn_name}",
                    location=loc,
                    metadata={
                        "sap_object_type": "FUNCTION_MODULE",
                        "semantic_key": sem_key,
                    },
                )
            )

        return SymbolExtractionResult(
            entities=entities,
            relationships=[],
            parse_status=ParseStatus.CLEAN,
        )

    def _fallback_single_chunk(self, document: SemanticDocument) -> List[SemanticChunk]:
        doc_id = document.document_id
        sem_key = "sap_object:abap_program"
        content_hash = hashlib.sha256(document.sanitized_content.encode("utf-8")).hexdigest()
        chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)
        uri = document.metadata.source_uri if document.metadata else ""
        loc = SourceLocation(
            location_type="sap",
            uri=uri,
        )
        lineage = ChunkLineage(
            source_hash=content_hash,
            chunk_hash=content_hash,
            sequence_index=0,
            location=loc,
        )
        return [
            SemanticChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                sanitized_content=document.sanitized_content,
                metadata=document.metadata,
                lineage=lineage,
            )
        ]
