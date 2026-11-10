"""Tree-sitter AST Code Chunker & Isolation Boundary.

Parses source code documents into structural AST chunks, entities, relationships,
and diagnostics while preserving standard library pipeline isolation.
"""

from dataclasses import asdict
import hashlib
import importlib
from typing import Any, Dict, List, Optional, Tuple

from md_generator.lineage.ids import generate_chunk_id
from md_generator.semantic.chunkers.base import BaseChunker, ParseStatus, SemanticDiagnostic, SymbolExtractionResult
from md_generator.semantic.chunkers.identity import (
    EntityType,
    RelationshipType,
    SymbolIdentity,
    compute_fqn,
)
from md_generator.semantic.chunkers.languages.base import LanguageCapability
from md_generator.semantic.chunkers.languages import (
    PYTHON_CAPABILITY,
    JAVA_CAPABILITY,
    TYPESCRIPT_CAPABILITY,
    GO_CAPABILITY,
    CPP_CAPABILITY,
    CSHARP_CAPABILITY,
)
from md_generator.semantic.model.schema import (
    CanonicalMetadata,
    ChunkLineage,
    Entity,
    Relationship,
    SemanticChunk,
    SemanticDocument,
    SourceLocation,
)

# Tree-sitter import isolation check
_TREE_SITTER_AVAILABLE: bool = False
try:
    import tree_sitter  # type: ignore
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    tree_sitter = None  # type: ignore


# Language grammar loader registry
_LANGUAGE_GRAMMAR_MAP: Dict[str, Tuple[str, str, LanguageCapability]] = {
    "python": ("tree_sitter_python", "language", PYTHON_CAPABILITY),
    "py": ("tree_sitter_python", "language", PYTHON_CAPABILITY),
    "java": ("tree_sitter_java", "language", JAVA_CAPABILITY),
    "typescript": ("tree_sitter_typescript", "language_typescript", TYPESCRIPT_CAPABILITY),
    "javascript": ("tree_sitter_typescript", "language_typescript", TYPESCRIPT_CAPABILITY),
    "ts": ("tree_sitter_typescript", "language_typescript", TYPESCRIPT_CAPABILITY),
    "js": ("tree_sitter_typescript", "language_typescript", TYPESCRIPT_CAPABILITY),
    "tsx": ("tree_sitter_typescript", "language_tsx", TYPESCRIPT_CAPABILITY),
    "jsx": ("tree_sitter_typescript", "language_tsx", TYPESCRIPT_CAPABILITY),
    "go": ("tree_sitter_go", "language", GO_CAPABILITY),
    "golang": ("tree_sitter_go", "language", GO_CAPABILITY),
    "cpp": ("tree_sitter_cpp", "language", CPP_CAPABILITY),
    "c++": ("tree_sitter_cpp", "language", CPP_CAPABILITY),
    "c": ("tree_sitter_cpp", "language", CPP_CAPABILITY),
    "csharp": ("tree_sitter_c_sharp", "language", CSHARP_CAPABILITY),
    "c#": ("tree_sitter_c_sharp", "language", CSHARP_CAPABILITY),
    "cs": ("tree_sitter_c_sharp", "language", CSHARP_CAPABILITY),
}


def _get_tree_sitter_language(lang_name: str) -> Tuple[Optional[Any], Optional[LanguageCapability]]:
    """Attempt to dynamically load tree-sitter Language instance and capability metadata."""
    if not _TREE_SITTER_AVAILABLE or tree_sitter is None:
        return None, None

    normalized = lang_name.strip().lower()
    if normalized not in _LANGUAGE_GRAMMAR_MAP:
        return None, None

    module_name, func_name, capability = _LANGUAGE_GRAMMAR_MAP[normalized]
    try:
        mod = importlib.import_module(module_name)
        fn = getattr(mod, func_name, None)
        if fn is None:
            return None, capability
        raw_lang = fn()
        lang_obj = tree_sitter.Language(raw_lang)
        return lang_obj, capability
    except Exception:
        return None, capability


class CodeChunker:
    """Tree-sitter AST Code Chunker for multi-language source code documents."""

    def __init__(self, chunker_version: str = "1.0"):
        self.chunker_version = chunker_version

    def supports(self, source_type: str) -> bool:
        """Check if source_type or extension is supported by CodeChunker."""
        st = source_type.strip().lower()
        if st in _LANGUAGE_GRAMMAR_MAP:
            return True
        if st.startswith("text/x-") or st.startswith("application/x-"):
            for lang in _LANGUAGE_GRAMMAR_MAP:
                if lang in st:
                    return True
        return False

    def chunk_document(self, document: SemanticDocument) -> List[SemanticChunk]:
        """Parse document code into structural SemanticChunks."""
        lang_name = self._resolve_language_name(document)
        lang_obj, capability = _get_tree_sitter_language(lang_name)

        if lang_obj is None:
            return self._fallback_single_chunk(document, lang_name)

        content_bytes = document.sanitized_content.encode("utf-8")
        parser = tree_sitter.Parser(lang_obj)
        tree = parser.parse(content_bytes)

        chunks: List[SemanticChunk] = []
        self._traverse_tree_for_chunks(
            node=tree.root_node,
            content_bytes=content_bytes,
            document=document,
            language=lang_name,
            capability=capability,
            parent_chunk_id=None,
            parent_semantic_key=None,
            chunks=chunks,
        )

        if not chunks:
            return self._fallback_single_chunk(document, lang_name)

        return chunks

    def extract_symbols(self, document: SemanticDocument) -> SymbolExtractionResult:
        """Extract domain Entities, Relationships, and Diagnostics from document AST."""
        lang_name = self._resolve_language_name(document)
        lang_obj, capability = _get_tree_sitter_language(lang_name)

        diagnostics: List[SemanticDiagnostic] = []
        if not _TREE_SITTER_AVAILABLE:
            diagnostics.append(
                SemanticDiagnostic(
                    severity="WARNING",
                    code="UNSUPPORTED_GRAMMAR",
                    message="Tree-sitter library is not installed in environment.",
                    parser="tree-sitter",
                )
            )
            return SymbolExtractionResult(diagnostics=diagnostics, parse_status=ParseStatus.FAILED)

        if lang_obj is None:
            diagnostics.append(
                SemanticDiagnostic(
                    severity="WARNING",
                    code="UNSUPPORTED_GRAMMAR",
                    message=f"Tree-sitter grammar for language '{lang_name}' is not available.",
                    parser="tree-sitter",
                )
            )
            return SymbolExtractionResult(diagnostics=diagnostics, parse_status=ParseStatus.FAILED)

        content_bytes = document.sanitized_content.encode("utf-8")
        parser = tree_sitter.Parser(lang_obj)
        tree = parser.parse(content_bytes)

        parse_status = ParseStatus.CLEAN
        if tree.root_node.has_error:
            parse_status = ParseStatus.RECOVERED
            uri = document.metadata.source_uri if document.metadata else ""
            diagnostics.append(
                SemanticDiagnostic(
                    severity="WARNING",
                    code="SYNTAX_ERROR",
                    message=f"Source file '{uri}' contains syntax error nodes.",
                    source_location=SourceLocation(
                        location_type="code",
                        uri=uri,
                        line_start=1,
                        line_end=tree.root_node.end_point[0] + 1,
                    ),
                    parser="tree-sitter",
                )
            )

        entities: List[Entity] = []
        relationships: List[Relationship] = []

        self._extract_entities_and_relationships(
            node=tree.root_node,
            content_bytes=content_bytes,
            document=document,
            language=lang_name,
            capability=capability,
            parent_entity=None,
            entities=entities,
            relationships=relationships,
            diagnostics=diagnostics,
        )

        return SymbolExtractionResult(
            entities=entities,
            relationships=relationships,
            diagnostics=diagnostics,
            parse_status=parse_status,
        )

    # Private helper methods
    def _resolve_language_name(self, document: SemanticDocument) -> str:
        if document.metadata:
            if document.metadata.language:
                return str(document.metadata.language).strip().lower()
            if document.metadata.source_type:
                st = document.metadata.source_type.strip().lower()
                if st in _LANGUAGE_GRAMMAR_MAP:
                    return st
                if "." in st:
                    ext = st.split(".")[-1]
                    if ext in _LANGUAGE_GRAMMAR_MAP:
                        return ext
        return "python"

    def _fallback_single_chunk(self, document: SemanticDocument, language: str) -> List[SemanticChunk]:
        doc_id = document.document_id
        sem_key = f"module:{document.metadata.symbol_name if document.metadata and document.metadata.symbol_name else 'module'}"
        content_hash = hashlib.sha256(document.sanitized_content.encode("utf-8")).hexdigest()
        chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)
        uri = document.metadata.source_uri if document.metadata else ""
        lines = document.sanitized_content.splitlines()

        loc = SourceLocation(
            location_type="code",
            uri=uri,
            line_start=1,
            line_end=len(lines) if lines else 1,
            column_start=1,
            column_end=len(lines[-1]) + 1 if lines else 1,
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

    def _traverse_tree_for_chunks(
        self,
        node: Any,
        content_bytes: bytes,
        document: SemanticDocument,
        language: str,
        capability: Optional[LanguageCapability],
        parent_chunk_id: Optional[str],
        parent_semantic_key: Optional[str],
        chunks: List[SemanticChunk],
    ) -> None:
        if node.is_error or node.type == "ERROR":
            return

        is_symbol_node, symbol_kind, local_name = self._identify_symbol_node(node, content_bytes, language)
        current_chunk_id = parent_chunk_id
        current_sem_key = parent_semantic_key

        if is_symbol_node and local_name:
            identity = compute_fqn(
                language=language,
                symbol_kind=symbol_kind,
                local_name=local_name,
                parent_symbol=parent_semantic_key.split(":")[-1] if parent_semantic_key else None,
            )
            sem_key = identity.compute_semantic_key()
            doc_id = document.document_id

            node_text = content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            content_hash = hashlib.sha256(node_text.encode("utf-8")).hexdigest()
            chunk_id = generate_chunk_id(doc_id, sem_key, content_hash)

            uri = document.metadata.source_uri if document.metadata else ""
            loc = SourceLocation(
                location_type="code",
                uri=uri,
                symbol=local_name,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                column_start=node.start_point[1] + 1,
                column_end=node.end_point[1] + 1,
            )
            lineage = ChunkLineage(
                source_hash=content_hash,
                chunk_hash=content_hash,
                parent_chunk_id=parent_chunk_id,
                sequence_index=len(chunks),
                location=loc,
            )

            chunk_metadata = None
            if document.metadata:
                chunk_metadata = CanonicalMetadata(
                    system=document.metadata.system,
                    domain=document.metadata.domain,
                    module=document.metadata.module,
                    source_type=document.metadata.source_type,
                    source_uri=document.metadata.source_uri,
                    source_path=document.metadata.source_path,
                    language=language,
                    symbol_name=identity.qualified_name,
                )

            chunk = SemanticChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                sanitized_content=node_text,
                metadata=chunk_metadata,
                lineage=lineage,
            )
            chunks.append(chunk)

            current_chunk_id = chunk_id
            current_sem_key = sem_key

        for child in node.named_children:
            self._traverse_tree_for_chunks(
                node=child,
                content_bytes=content_bytes,
                document=document,
                language=language,
                capability=capability,
                parent_chunk_id=current_chunk_id,
                parent_semantic_key=current_sem_key,
                chunks=chunks,
            )

    def _extract_entities_and_relationships(
        self,
        node: Any,
        content_bytes: bytes,
        document: SemanticDocument,
        language: str,
        capability: Optional[LanguageCapability],
        parent_entity: Optional[Entity],
        entities: List[Entity],
        relationships: List[Relationship],
        diagnostics: List[SemanticDiagnostic],
    ) -> None:
        if node.is_error or node.type == "ERROR":
            return

        is_symbol_node, symbol_kind, local_name = self._identify_symbol_node(node, content_bytes, language)
        current_entity = parent_entity

        if is_symbol_node and local_name:
            identity = compute_fqn(
                language=language,
                symbol_kind=symbol_kind,
                local_name=local_name,
                parent_symbol=parent_entity.qualified_name if parent_entity else None,
            )
            sem_key = identity.compute_semantic_key()
            entity_type_str = self._map_to_entity_type(symbol_kind)

            entity_id = hashlib.sha256(
                f"{document.document_id}:{sem_key}".encode("utf-8")
            ).hexdigest()

            uri = document.metadata.source_uri if document.metadata else ""
            loc = SourceLocation(
                location_type="code",
                uri=uri,
                symbol=local_name,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                column_start=node.start_point[1] + 1,
                column_end=node.end_point[1] + 1,
            )

            entity = Entity(
                entity_id=entity_id,
                entity_type=entity_type_str,
                name=local_name,
                qualified_name=identity.qualified_name,
                location=loc,
                metadata={
                    "language": language,
                    "qualification_strategy": identity.qualification_strategy,
                    "semantic_key": sem_key,
                },
            )
            entities.append(entity)
            current_entity = entity

            # Parent-child CONTAINS relationship
            if parent_entity:
                rel_id = hashlib.sha256(
                    f"{parent_entity.entity_id}:CONTAINS:{entity.entity_id}".encode("utf-8")
                ).hexdigest()
                rel = Relationship(
                    relationship_id=rel_id,
                    source_entity_id=parent_entity.entity_id,
                    target_entity_id=entity.entity_id,
                    relationship_type=RelationshipType.CONTAINS.value,
                    confidence=1.0,
                    provenance={
                        "resolution_status": "resolved",
                        "provenance": "tree-sitter-structural",
                    },
                )
                relationships.append(rel)

        # Extract function call relationships
        if node.type in ("call", "method_invocation", "call_expression"):
            call_target = self._extract_call_target(node, content_bytes)
            if call_target and current_entity:
                target_hex_id = hashlib.sha256(f"unresolved:{call_target}".encode("utf-8")).hexdigest()
                rel_id = hashlib.sha256(
                    f"{current_entity.entity_id}:CALLS:{target_hex_id}".encode("utf-8")
                ).hexdigest()
                relationships.append(
                    Relationship(
                        relationship_id=rel_id,
                        source_entity_id=current_entity.entity_id,
                        target_entity_id=target_hex_id,
                        relationship_type=RelationshipType.CALLS.value,
                        confidence=0.8,
                        provenance={
                            "resolution_status": "unresolved",
                            "call_target": call_target,
                            "provenance": "tree-sitter-syntactic-call",
                        },
                    )
                )

        for child in node.named_children:
            self._extract_entities_and_relationships(
                node=child,
                content_bytes=content_bytes,
                document=document,
                language=language,
                capability=capability,
                parent_entity=current_entity,
                entities=entities,
                relationships=relationships,
                diagnostics=diagnostics,
            )

    def _identify_symbol_node(self, node: Any, content_bytes: bytes, language: str) -> Tuple[bool, str, str]:
        nt = node.type
        if nt in ("class_definition", "class_declaration"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else ""
            return True, "class", name
        elif nt in ("function_definition", "function_declaration"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else ""
            return True, "function", name
        elif nt in ("method_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else ""
            return True, "method", name
        elif nt in ("type_spec", "struct_spec"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else ""
            return True, "struct", name
        elif nt in ("interface_declaration",):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else ""
            return True, "interface", name
        elif nt in ("enum_declaration",):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else ""
            return True, "enum", name

        return False, "", ""

    def _map_to_entity_type(self, symbol_kind: str) -> str:
        mapping = {
            "class": EntityType.CLASS.value,
            "function": EntityType.FUNCTION.value,
            "method": EntityType.METHOD.value,
            "struct": EntityType.STRUCT.value,
            "interface": EntityType.INTERFACE.value,
            "enum": EntityType.ENUM.value,
            "module": EntityType.MODULE.value,
        }
        return mapping.get(symbol_kind.lower(), EntityType.FUNCTION.value)

    def _extract_call_target(self, node: Any, content_bytes: bytes) -> str:
        fn_node = node.child_by_field_name("function") or node.child_by_field_name("name")
        if fn_node and fn_node.text:
            return fn_node.text.decode("utf-8", errors="replace")
        return ""
