from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_generator.codeflow.enterprise_ir.graph import EnterpriseIR


@dataclass
class SymbolRecord:
    name: str
    kind: str  # class, method, function, interface, struct
    line: int
    column: int
    class_name: str | None = None
    fqn: str | None = None


@dataclass
class ImportRecord:
    source_file: str
    imported_name: str
    import_path: str
    line: int
    is_relative: bool = False


@dataclass
class RawDependency:
    name: str
    version: str
    scope: str
    group: str | None = None
    artifact: str | None = None
    repo_url: str | None = None
    license_name: str | None = None
    optional: bool = False
    transitive: bool = False


@dataclass
class ConfigUsage:
    key: str
    source_file: str
    line: int
    usage_type: str  # Value, Env, Property, etc.
    class_name: str | None = None
    field_name: str | None = None


@dataclass
class RawQuery:
    query_text: str
    operation: str  # READ, WRITE, etc.
    database_type: str
    dialect: str
    is_transactional: bool
    is_read_only: bool
    line: int
    tables: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)


@dataclass
class RawResource:
    resource_type: str
    uri: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RawEvent:
    topic: str | None
    queue: str | None
    broker: str
    is_publisher: bool
    is_consumer: bool
    payload_type: str | None = None
    handler_method: str | None = None


class ParserBackendRegistry:
    def __init__(self) -> None:
        self._backends = ["native", "treesitter", "external", "regex"]

    def list_backends(self) -> list[str]:
        return list(self._backends)


class LanguageAdapter(ABC):
    @property
    @abstractmethod
    def language(self) -> str:
        """Returns target language name."""
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Returns extensions supported by this adapter."""
        ...

    @property
    @abstractmethod
    def parser_backends(self) -> list[str]:
        """Returns parser backends supported, in priority order."""
        ...

    @abstractmethod
    def discover(self, workspace_root: Path) -> list[Path]:
        """Finds language-specific files in the workspace."""
        ...

    @abstractmethod
    def extract_symbols(self, file_path: Path, backend: str) -> list[SymbolRecord]:
        """Extracts declared types, classes, methods and functions."""
        ...

    @abstractmethod
    def extract_imports(self, file_path: Path, backend: str) -> list[ImportRecord]:
        """Extracts file imports/dependencies."""
        ...

    @abstractmethod
    def extract_dependencies(self, file_path: Path, backend: str) -> list[RawDependency]:
        """Extracts third-party package dependencies."""
        ...

    @abstractmethod
    def extract_config_usage(self, file_path: Path, backend: str) -> list[ConfigUsage]:
        """Extracts properties references in source files."""
        ...

    @abstractmethod
    def extract_queries(self, file_path: Path, backend: str) -> list[RawQuery]:
        """Extracts embedded and standalone database operations."""
        ...

    @abstractmethod
    def extract_external_resources(self, file_path: Path, backend: str) -> list[RawResource]:
        """Extracts client connections and external API integrations."""
        ...

    @abstractmethod
    def extract_events(self, file_path: Path, backend: str) -> list[RawEvent]:
        """Extracts message brokers publishers/listeners."""
        ...

    @abstractmethod
    def build_ir(self, file_path: Path, backend: str, extracted_data: dict[str, Any]) -> EnterpriseIR:
        """Constructs canonical EnterpriseIR nodes from extracted records."""
        ...
