from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# SQL / Mongo / Oracle features (unchanged names — do not rename).
_LEGACY_FEATURES = frozenset(
    {
        "tables",
        "views",
        "indexes",
        "procedures",
        "functions",
        "triggers",
        "sequences",
        "partitions",
        "synonyms",
        "dependencies",
        "oracle_packages",
        "oracle_clusters",
        "mongodb_collections",
        "erd",
    }
)

# Elasticsearch / OpenSearch export features (opt-in via database.type: elasticsearch).
ELASTICSEARCH_FEATURES = frozenset(
    {
        "elasticsearch_indices",
        "elasticsearch_data_streams",
        "elasticsearch_component_templates",
        "elasticsearch_index_templates",
        "elasticsearch_ingest_pipelines",
        "elasticsearch_ilm_policies",
        "elasticsearch_field_caps",
        "elasticsearch_snapshot_repositories",
        "elasticsearch_search_templates",
        "elasticsearch_search_architecture",
        # Reserved for future security export (validated but not exported yet).
        "elasticsearch_security_roles",
        "elasticsearch_security_users",
        "elasticsearch_security_api_keys",
    }
)

FEATURES = _LEGACY_FEATURES | ELASTICSEARCH_FEATURES


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool
    default: str | None = None
    comment: str | None = None


@dataclass(frozen=True)
class ForeignKeyInfo:
    name: str | None
    constrained_columns: tuple[str, ...]
    referred_schema: str | None
    referred_table: str
    referred_columns: tuple[str, ...]


@dataclass(frozen=True)
class IndexInfo:
    name: str
    unique: bool
    columns: tuple[str, ...]
    definition: str | None = None


@dataclass(frozen=True)
class TableInfo:
    schema: str
    name: str
    comment: str | None = None


@dataclass(frozen=True)
class TableDetail:
    table: TableInfo
    columns: tuple[ColumnInfo, ...]
    primary_key: tuple[str, ...]
    foreign_keys: tuple[ForeignKeyInfo, ...]


@dataclass(frozen=True)
class ViewInfo:
    schema: str
    name: str
    definition: str | None


@dataclass(frozen=True)
class RoutineInfo:
    kind: str  # FUNCTION | PROCEDURE
    schema: str
    name: str
    language: str | None
    definition: str | None
    comment: str | None = None


@dataclass(frozen=True)
class SynonymInfo:
    schema: str
    name: str
    base_object: str
    comment: str | None = None


@dataclass(frozen=True)
class DependencyEdge:
    referencing_schema: str
    referencing_name: str
    referencing_kind: str
    referenced_schema: str
    referenced_name: str
    referenced_kind: str


@dataclass(frozen=True)
class TriggerInfo:
    schema: str
    name: str
    table_schema: str
    table_name: str
    definition: str | None
    timing: str | None = None
    events: str | None = None


@dataclass(frozen=True)
class SequenceInfo:
    schema: str
    name: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PartitionInfo:
    schema: str
    parent_table: str
    name: str
    method: str | None = None
    expression: str | None = None


@dataclass(frozen=True)
class PackageInfo:
    schema: str
    name: str
    spec_source: str | None = None
    body_source: str | None = None


@dataclass(frozen=True)
class ClusterInfo:
    schema: str
    name: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MongoIndexInfo:
    name: str
    keys: dict[str, Any]
    unique: bool = False


@dataclass(frozen=True)
class MongoCollectionInfo:
    name: str
    inferred_schema: dict[str, Any]
    indexes: tuple[MongoIndexInfo, ...]
    sample_size: int


@dataclass(frozen=True)
class ElasticsearchIndexInfo:
    name: str
    aliases: tuple[str, ...]
    mappings: dict[str, Any]
    settings: dict[str, Any]
    shard_config: dict[str, Any]
    health: str | None = None
    doc_count: int | None = None
    store_size: str | None = None
    primary_shards: int | None = None
    replica_shards: int | None = None
    field_caps: dict[str, Any] | None = None


@dataclass(frozen=True)
class ElasticsearchDataStreamInfo:
    name: str
    indices: tuple[str, ...]
    template: str | None
    generation: int | None
    definition: dict[str, Any]


@dataclass(frozen=True)
class ElasticsearchComponentTemplateInfo:
    name: str
    template: dict[str, Any]


@dataclass(frozen=True)
class ElasticsearchPipelineInfo:
    name: str
    definition: dict[str, Any]


@dataclass(frozen=True)
class ElasticsearchIndexTemplateInfo:
    name: str
    index_patterns: tuple[str, ...]
    priority: int | None
    template: dict[str, Any]
    composed_of: tuple[str, ...] | None = None
    legacy: bool = False


@dataclass(frozen=True)
class ElasticsearchIlmPolicyInfo:
    name: str
    policy: dict[str, Any]
    source: str = "ilm"  # ilm | ism


@dataclass(frozen=True)
class ElasticsearchSnapshotRepositoryInfo:
    name: str
    repository_type: str
    settings: dict[str, Any]
    operational: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None


@dataclass(frozen=True)
class ElasticsearchSearchTemplateInfo:
    name: str
    lang: str
    definition: dict[str, Any]
    param_keys: tuple[str, ...] = ()
    source_length: int | None = None
    source_preview: str | None = None
    source_truncated: bool = False
    diagnostics: str | None = None


@dataclass(frozen=True)
class RunMetadata:
    db_type: str
    uri_display: str  # redacted
    schema: str | None
    database: str | None  # Mongo
    included_features: tuple[str, ...]
    limits: dict[str, Any]
    generated_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    erd_artifacts: tuple[str, ...] = ()
    erd_note: str | None = None
    erd_engine: str | None = None  # graphviz | mermaid_py | mermaid_text
    readme_feature_merge: str = "none"  # none | inline | toc
    combined_readme_paths: tuple[str, ...] = ()
    cluster_name: str | None = None  # Elasticsearch / OpenSearch
