from __future__ import annotations

"""ConverterAdapter Protocol & Multi-Language ConverterRegistry.

Phase 0C-2 Implementation: Converter adapter boundary, multi-language
extension mapping, and 5-step deterministic dispatch precedence.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Union


class UnsupportedSourceError(Exception):
    """Raised when no registered adapter can handle the given source file."""

    pass


@dataclass
class ExtractionOutput:
    """Raw extraction payload produced by a ConverterAdapter."""

    raw_markdown: str
    source_uri: str
    source_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConverterAdapter(Protocol):
    """Protocol boundary wrapping native converters without direct code mutation."""

    def supports(self, source_type: str) -> bool:
        """Return True if this adapter supports the given source_type."""
        ...

    def extract(self, source_path: str) -> ExtractionOutput:
        """Extract content from source_path using the underlying converter engine."""
        ...


@dataclass
class RegistryEntry:
    source_type: str
    adapter: ConverterAdapter
    extensions: Set[str] = field(default_factory=set)
    exact_filenames: Set[str] = field(default_factory=set)
    signature_checker: Optional[Callable[[str], bool]] = None


class BaseTextAdapter:
    """Default fallback adapter for text-readable source files."""

    def __init__(self, source_type: str = "text.plain") -> None:
        self._source_type = source_type

    def supports(self, source_type: str) -> bool:
        return source_type == self._source_type or source_type.startswith("text.")

    def extract(self, source_path: str) -> ExtractionOutput:
        path = Path(source_path)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            content = f"<!-- Error reading file {path.name}: {e} -->"

        return ExtractionOutput(
            raw_markdown=content,
            source_uri=path.as_uri(),
            source_type=self._source_type,
            metadata={"file_name": path.name, "file_size_bytes": path.stat().st_size if path.exists() else 0},
        )


class CodeflowAdapter:
    """Adapter wrapping Codeflow multi-language source file reading."""

    def __init__(self, lang_key: str = "code") -> None:
        self.lang_key = lang_key
        self._source_type = f"code.{lang_key}"

    def supports(self, source_type: str) -> bool:
        return source_type == self._source_type

    def extract(self, source_path: str) -> ExtractionOutput:
        path = Path(source_path)
        content = path.read_text(encoding="utf-8", errors="replace")
        lang = self.lang_key
        md = f"``` {lang}\n{content}\n```\n"
        return ExtractionOutput(
            raw_markdown=md,
            source_uri=path.as_uri(),
            source_type=self._source_type,
            metadata={"language": lang, "lines": len(content.splitlines())},
        )


class ConverterRegistry:
    """Central registry resolving source adapters via 5-step deterministic precedence."""

    def __init__(self) -> None:
        self._entries: List[RegistryEntry] = []

    def register(
        self,
        source_type: str,
        adapter: ConverterAdapter,
        extensions: Optional[Set[str]] = None,
        exact_filenames: Optional[Set[str]] = None,
        signature_checker: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """Register a converter adapter with explicit dispatch triggers."""
        entry = RegistryEntry(
            source_type=source_type,
            adapter=adapter,
            extensions={ext.lower() for ext in (extensions or set())},
            exact_filenames={fn.lower() for fn in (exact_filenames or set())},
            signature_checker=signature_checker,
        )
        # Store newest registrations first so user registrations take precedence
        self._entries.insert(0, entry)

    def resolve(self, source_path: str, source_type: Optional[str] = None) -> ConverterAdapter:
        """Resolve adapter using 5-step deterministic dispatch algorithm.

        1. Explicit source_type argument match
        2. Registered exact filename or multi-part extension match (.openapi.json, .edmx)
        3. Content / signature detection
        4. Extension fallback (.py, .java, .pdf)
        5. UnsupportedSourceError fallback
        """
        path = Path(source_path)
        file_name_lower = path.name.lower()
        ext_lower = path.suffix.lower()

        # Step 1: Explicit source_type match
        if source_type:
            for entry in self._entries:
                if entry.source_type == source_type:
                    return entry.adapter

        # Step 2: Exact filename / multi-part pattern match
        for entry in self._entries:
            for fn in entry.exact_filenames:
                if file_name_lower == fn or file_name_lower.endswith(fn):
                    return entry.adapter

        # Step 3: Content / signature detection
        if path.exists() and path.is_file():
            for entry in self._entries:
                if entry.signature_checker:
                    try:
                        header = path.read_text(encoding="utf-8", errors="ignore")[:2048]
                        if entry.signature_checker(header):
                            return entry.adapter
                    except Exception:
                        pass

        # Step 4: Extension fallback
        if ext_lower:
            for entry in self._entries:
                if ext_lower in entry.extensions:
                    return entry.adapter

        # Step 5: Fallback error
        raise UnsupportedSourceError(
            f"No registered converter adapter found for file '{source_path}' (source_type={source_type})"
        )

    @classmethod
    def create_default(cls) -> ConverterRegistry:
        """Factory returning a ConverterRegistry pre-configured with all supported extension mappings."""
        registry = cls()

        # Codeflow Multi-Language Registrations (matching codeflow/lang_dispatch.py)
        code_langs: Dict[str, Set[str]] = {
            "python": {".py"},
            "java": {".java"},
            "javascript": {".js", ".jsx", ".mjs", ".cjs"},
            "typescript": {".ts", ".mts", ".cts"},
            "tsx": {".tsx"},
            "cpp": {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"},
            "go": {".go"},
            "php": {".php"},
            "rust": {".rs"},
            "kotlin": {".kt", ".kts"},
            "csharp": {".cs"},
            "swift": {".swift"},
            "ruby": {".rb"},
            "lua": {".lua"},
            "scala": {".scala", ".sc"},
            "zig": {".zig"},
        }
        for lang, exts in code_langs.items():
            registry.register(
                source_type=f"code.{lang}",
                adapter=CodeflowAdapter(lang_key=lang),
                extensions=exts,
            )

        # OpenAPI / Swagger
        def openapi_sig(header: str) -> bool:
            h = header.lower()
            return "openapi" in h or "swagger" in h

        registry.register(
            source_type="api.openapi",
            adapter=BaseTextAdapter("api.openapi"),
            exact_filenames={".openapi.json", ".openapi.yaml", ".swagger.json", ".swagger.yaml"},
            signature_checker=openapi_sig,
        )

        # OData EDMX
        def odata_sig(header: str) -> bool:
            return "<edmx:edmx" in header.lower() or "schemas.microsoft.com/ado/" in header.lower()

        registry.register(
            source_type="api.odata",
            adapter=BaseTextAdapter("api.odata"),
            exact_filenames={".edmx"},
            extensions={".edmx"},
            signature_checker=odata_sig,
        )

        # SAP / ABAP
        registry.register(
            source_type="sap.abap",
            adapter=BaseTextAdapter("sap.abap"),
            extensions={".abap", ".idoc", ".bapi"},
        )

        # Database / SQL
        registry.register(
            source_type="db.sql",
            adapter=BaseTextAdapter("db.sql"),
            extensions={".sql", ".db", ".sqlite"},
        )

        # Document Formats (Text fallback in 0C; specialized converters when present)
        registry.register(
            source_type="doc.pdf",
            adapter=BaseTextAdapter("doc.pdf"),
            extensions={".pdf"},
        )
        registry.register(
            source_type="doc.word",
            adapter=BaseTextAdapter("doc.word"),
            extensions={".docx", ".doc"},
        )
        registry.register(
            source_type="doc.ppt",
            adapter=BaseTextAdapter("doc.ppt"),
            extensions={".pptx", ".ppt"},
        )
        registry.register(
            source_type="doc.xlsx",
            adapter=BaseTextAdapter("doc.xlsx"),
            extensions={".xlsx", ".xls"},
        )

        # General Text / MD / JSON / XML / Logs
        registry.register(
            source_type="text.plain",
            adapter=BaseTextAdapter("text.plain"),
            extensions={".txt", ".md", ".json", ".xml", ".log", ".jsonl", ".otel"},
        )

        return registry
