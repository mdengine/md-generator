from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

# Graph Schema Version definition
GRAPH_SCHEMA_VERSION = "1.0"


class NodeType(str, Enum):
    FILE = "FILE"
    PACKAGE = "PACKAGE"
    MODULE = "MODULE"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    METHOD = "METHOD"
    FUNCTION = "FUNCTION"
    QUERY = "QUERY"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    VIEW = "VIEW"
    QUEUE = "QUEUE"
    TOPIC = "TOPIC"
    CONFIG = "CONFIG"
    DEPENDENCY = "DEPENDENCY"
    RESOURCE = "RESOURCE"
    EVENT = "EVENT"
    API = "API"


class EdgeType(str, Enum):
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    CONFIGURES = "CONFIGURES"
    USES_LIBRARY = "USES_LIBRARY"
    USES_CONFIGURATION = "USES_CONFIGURATION"
    READS_TABLE = "READS_TABLE"
    WRITES_TABLE = "WRITES_TABLE"
    READS_COLLECTION = "READS_COLLECTION"
    WRITES_COLLECTION = "WRITES_COLLECTION"
    PUBLISHES_EVENT = "PUBLISHES_EVENT"
    CONSUMES_EVENT = "CONSUMES_EVENT"
    FILE_DEPENDS_ON = "FILE_DEPENDS_ON"
    METHOD_DEPENDS_ON = "METHOD_DEPENDS_ON"
    CALLS_EXTERNAL_API = "CALLS_EXTERNAL_API"
    USES_STORAGE = "USES_STORAGE"
    USES_QUEUE = "USES_QUEUE"


class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class PluginCategory(str, Enum):
    DISCOVERY = "DISCOVERY"
    PARSER = "PARSER"
    NORMALIZER = "NORMALIZER"
    ANALYZER = "ANALYZER"
    GRAPH = "GRAPH"
    EXPORTER = "EXPORTER"


@dataclass
class Diagnostic:
    severity: DiagnosticSeverity
    file: str
    line: int | None
    message: str
    plugin: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


@dataclass
class ParserCapability:
    language: str
    backend: str
    supports_cfg: bool
    supports_runtime: bool
    supports_incremental: bool


@dataclass
class PluginDependency:
    plugin_name: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class AnalysisStatistics:
    files_scanned: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    parser_failures: int = 0
    unknown_language: int = 0
    unknown_query: int = 0
    unknown_dependency: int = 0
    unknown_configuration: int = 0
    nodes_created: int = 0
    nodes_reused: int = 0
    edges_created: int = 0
    execution_time_seconds: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class RepositoryFingerprint:
    repository: str
    branch: str
    commit: str
    language_hash: str
    dependency_hash: str
    configuration_hash: str
    graph_hash: str


@dataclass
class GraphMetadata:
    scan_id: str
    repository: str
    branch: str
    commit: str
    version: str = "1.0.0"
    schema_version: str = GRAPH_SCHEMA_VERSION
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


@dataclass
class NodeMetadata:
    id: str
    kind: NodeType
    language: str
    repository: str
    module: str | None
    file: str
    line: int | None
    column: int | None
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    parser: str
    backend: str
    version: str = "1.0.0"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeMetadata:
    edge_type: EdgeType
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    parser: str
    plugin: str
    language: str
    created_by: str = "central_graph_builder"
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    version: str = "1.0.0"


@dataclass
class BaseEntity:
    id: str  # Stable URI
    metadata: NodeMetadata
