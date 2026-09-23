"""SQL DDL database table and view domain chunker."""

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


class DBChunker:
    """Domain chunker for SQL DDL statements (CREATE TABLE, CREATE VIEW)."""

    def __init__(self, chunker_version: str = "1.0"):
        self.chunker_version = chunker_version

    def supports(self, source_type: str) -> bool:
        st = source_type.strip().lower()
        return "sql" in st or "ddl" in st or "db" in st or st.endswith(".sql")

    def chunk_document(self, document: SemanticDocument) -> List[SemanticChunk]:
        content = document.sanitized_content
        doc_id = document.document_id
        chunks: List[SemanticChunk] = []

        table_matches = re.finditer(
            r"(?i)CREATE\s+(TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"\[]?[\w\.]+\b[`\"\]]?)(.*?);",
            content,
            re.DOTALL,
        )
        for match in table_matches:
            obj_kind = match.group(1).lower()
            raw_name = match.group(2).strip("`\"[]")
            body = match.group(0)

            identity = compute_fqn("sql", obj_kind, raw_name)
            sem_key = identity.compute_semantic_key()
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)

            uri = document.metadata.source_uri if document.metadata else ""
            loc = SourceLocation(
                location_type="database",
                uri=uri,
                table=raw_name,
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
                    source_type="sql",
                    source_uri=document.metadata.source_uri,
                    table_name=raw_name,
                )

            chunks.append(
                SemanticChunk(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    sanitized_content=body,
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

        table_matches = re.finditer(
            r"(?i)CREATE\s+(TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"\[]?[\w\.]+\b[`\"\]]?)",
            content,
        )
        for match in table_matches:
            obj_kind = match.group(1).lower()
            raw_name = match.group(2).strip("`\"[]")
            sem_key = f"{obj_kind}:{raw_name}"
            entity_id = hashlib.sha256(f"{doc_id}:{sem_key}".encode("utf-8")).hexdigest()
            entity_type_str = EntityType.TABLE.value if obj_kind == "table" else EntityType.VIEW.value

            uri = document.metadata.source_uri if document.metadata else ""
            loc = SourceLocation(
                location_type="database",
                uri=uri,
                table=raw_name,
            )

            entities.append(
                Entity(
                    entity_id=entity_id,
                    entity_type=entity_type_str,
                    name=raw_name,
                    qualified_name=raw_name,
                    location=loc,
                    metadata={"object_kind": obj_kind, "semantic_key": sem_key},
                )
            )

        return SymbolExtractionResult(
            entities=entities,
            relationships=[],
            parse_status=ParseStatus.CLEAN,
        )

    def _fallback_single_chunk(self, document: SemanticDocument) -> List[SemanticChunk]:
        doc_id = document.document_id
        sem_key = "table:ddl_script"
        content_hash = hashlib.sha256(document.sanitized_content.encode("utf-8")).hexdigest()
        chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)
        uri = document.metadata.source_uri if document.metadata else ""
        loc = SourceLocation(
            location_type="database",
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
