"""ChunkerRegistry with strict resolution precedence and ambiguity protection."""

from typing import Dict, List, Optional
from md_generator.semantic.chunkers.base import BaseChunker
from md_generator.semantic.chunkers.code import CodeChunker
from md_generator.semantic.chunkers.openapi import OpenAPIChunker
from md_generator.semantic.chunkers.sap import SAPChunker
from md_generator.semantic.chunkers.db import DBChunker


class AmbiguousChunkerError(Exception):
    """Raised when multiple chunkers claim the same source_type at equal priority level."""
    pass


class ChunkerRegistry:
    """Registry maintaining domain chunkers with deterministic precedence resolution."""

    def __init__(self):
        self._explicit_map: Dict[str, BaseChunker] = {}
        self._registered_chunkers: List[BaseChunker] = []

    def register(self, chunker: BaseChunker, explicit_source_type: Optional[str] = None) -> None:
        """Register a chunker instance with optional explicit source_type binding."""
        if explicit_source_type:
            st = explicit_source_type.strip().lower()
            if st in self._explicit_map and self._explicit_map[st] is not chunker:
                raise AmbiguousChunkerError(
                    f"Ambiguous registration: source_type '{st}' is already bound to {self._explicit_map[st]}."
                )
            self._explicit_map[st] = chunker

        if chunker not in self._registered_chunkers:
            self._registered_chunkers.append(chunker)

    def resolve(self, source_type: str) -> Optional[BaseChunker]:
        """Resolve chunker for the given source_type according to priority precedence."""
        if not source_type:
            return None

        st = source_type.strip().lower()

        # Step 1: Explicit binding
        if st in self._explicit_map:
            return self._explicit_map[st]

        # Step 2: Domain/Code chunker support check
        matching: List[BaseChunker] = []
        for chunker in self._registered_chunkers:
            if chunker.supports(st):
                matching.append(chunker)

        if not matching:
            return None

        if len(matching) == 1:
            return matching[0]

        # If domain chunker and generic code chunker both match, prefer domain chunker over CodeChunker
        domain_matches = [c for c in matching if not isinstance(c, CodeChunker)]
        if len(domain_matches) == 1:
            return domain_matches[0]
        elif len(domain_matches) > 1:
            raise AmbiguousChunkerError(
                f"Multiple domain chunkers match source_type '{source_type}': {[type(c).__name__ for c in domain_matches]}"
            )

        return matching[0]

    @classmethod
    def get_default(cls) -> "ChunkerRegistry":
        """Create and populate default ChunkerRegistry with all built-in chunkers."""
        registry = cls()
        registry.register(OpenAPIChunker())
        registry.register(SAPChunker())
        registry.register(DBChunker())
        registry.register(CodeChunker())
        return registry
