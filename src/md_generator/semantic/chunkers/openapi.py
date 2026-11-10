"""OpenAPI / Swagger domain chunker for endpoints and JSON/YAML schemas."""

import hashlib
import json
from typing import List
from md_generator.lineage.ids import generate_chunk_id
from md_generator.semantic.chunkers.base import SymbolExtractionResult, ParseStatus
from md_generator.semantic.chunkers.identity import EntityType, compute_fqn
from md_generator.semantic.model.schema import (
    CanonicalMetadata,
    ChunkLineage,
    Entity,
    Relationship,
    SemanticChunk,
    SemanticDocument,
    SourceLocation,
)


class OpenAPIChunker:
    """Domain chunker for OpenAPI endpoints, operations, and schemas."""

    def __init__(self, chunker_version: str = "1.0"):
        self.chunker_version = chunker_version

    def supports(self, source_type: str) -> bool:
        st = source_type.strip().lower()
        return "openapi" in st or "swagger" in st or st.endswith(".json") or st.endswith(".yaml") or st.endswith(".yml")

    def chunk_document(self, document: SemanticDocument) -> List[SemanticChunk]:
        try:
            spec = json.loads(document.sanitized_content)
        except Exception:
            return self._fallback_single_chunk(document)

        if not isinstance(spec, dict) or "paths" not in spec:
            return self._fallback_single_chunk(document)

        chunks: List[SemanticChunk] = []
        doc_id = document.document_id
        paths = spec.get("paths", {})

        for path_str, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method_str, op_obj in methods.items():
                if method_str.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                    continue
                method_upper = method_str.upper()
                identity = compute_fqn("openapi", "endpoint", f"{method_upper}:{path_str}")
                sem_key = identity.compute_semantic_key()

                op_summary = op_obj.get("summary", "") if isinstance(op_obj, dict) else ""
                content_snippet = f"## {method_upper} {path_str}\n\n{op_summary}\n\n```json\n{json.dumps(op_obj, indent=2)}\n```"
                content_hash = hashlib.sha256(content_snippet.encode("utf-8")).hexdigest()
                chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)

                uri = document.metadata.source_uri if document.metadata else ""
                loc = SourceLocation(
                    location_type="openapi",
                    uri=uri,
                    endpoint=path_str,
                    http_method=method_upper,
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
                        source_type="openapi",
                        source_uri=document.metadata.source_uri,
                        api_method=method_upper,
                        api_path=path_str,
                    )

                chunks.append(
                    SemanticChunk(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        sanitized_content=content_snippet,
                        metadata=chunk_metadata,
                        lineage=lineage,
                    )
                )

        if not chunks:
            return self._fallback_single_chunk(document)

        return chunks

    def extract_symbols(self, document: SemanticDocument) -> SymbolExtractionResult:
        try:
            spec = json.loads(document.sanitized_content)
        except Exception:
            return SymbolExtractionResult(parse_status=ParseStatus.FAILED)

        if not isinstance(spec, dict) or "paths" not in spec:
            return SymbolExtractionResult(parse_status=ParseStatus.CLEAN)

        entities: List[Entity] = []
        relationships: List[Relationship] = []
        doc_id = document.document_id

        paths = spec.get("paths", {})
        for path_str, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method_str, op_obj in methods.items():
                if method_str.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                    continue
                method_upper = method_str.upper()
                canonical_name = f"{method_upper} {path_str}"
                sem_key = f"endpoint:{method_upper}:{path_str}"
                entity_id = hashlib.sha256(f"{doc_id}:{sem_key}".encode("utf-8")).hexdigest()

                uri = document.metadata.source_uri if document.metadata else ""
                loc = SourceLocation(
                    location_type="openapi",
                    uri=uri,
                    endpoint=path_str,
                    http_method=method_upper,
                )

                entities.append(
                    Entity(
                        entity_id=entity_id,
                        entity_type=EntityType.ENDPOINT.value,
                        name=canonical_name,
                        qualified_name=canonical_name,
                        location=loc,
                        metadata={
                            "method": method_upper,
                            "path": path_str,
                            "semantic_key": sem_key,
                        },
                    )
                )

        return SymbolExtractionResult(
            entities=entities,
            relationships=relationships,
            parse_status=ParseStatus.CLEAN,
        )

    def _fallback_single_chunk(self, document: SemanticDocument) -> List[SemanticChunk]:
        doc_id = document.document_id
        sem_key = "schema:openapi_root"
        content_hash = hashlib.sha256(document.sanitized_content.encode("utf-8")).hexdigest()
        chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)
        uri = document.metadata.source_uri if document.metadata else ""
        loc = SourceLocation(
            location_type="openapi",
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
