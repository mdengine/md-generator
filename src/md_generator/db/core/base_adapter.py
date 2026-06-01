from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from md_generator.db.core.models import (
    ClusterInfo,
    ColumnInfo,
    DependencyEdge,
    ElasticsearchComponentTemplateInfo,
    ElasticsearchDataStreamInfo,
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchIlmPolicyInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSlmPolicyInfo,
    ElasticsearchSnapshotRepositoryInfo,
    ForeignKeyInfo,
    IndexInfo,
    MongoCollectionInfo,
    PackageInfo,
    PartitionInfo,
    RoutineInfo,
    SequenceInfo,
    SynonymInfo,
    TableDetail,
    TableInfo,
    TriggerInfo,
    ViewInfo,
)


class BaseAdapter(ABC):
    """Introspection adapter; unsupported features return empty containers."""

    db_type: str

    @abstractmethod
    def validate_connection(self) -> None:
        """Raise if the database is unreachable."""

    @abstractmethod
    def close(self) -> None:
        """Release connections/clients."""

    def get_tables(self) -> list[TableInfo]:
        return []

    def get_table_detail(self, table: TableInfo) -> TableDetail:
        raise NotImplementedError

    def get_indexes(self, table: TableInfo) -> list[IndexInfo]:
        return []

    def get_views(self) -> list[ViewInfo]:
        return []

    def get_functions(self) -> list[RoutineInfo]:
        return []

    def get_procedures(self) -> list[RoutineInfo]:
        return []

    def get_triggers(self) -> list[TriggerInfo]:
        return []

    def get_sequences(self) -> list[SequenceInfo]:
        return []

    def get_partitions(self) -> list[PartitionInfo]:
        return []

    def get_packages(self) -> list[PackageInfo]:
        return []

    def get_clusters(self) -> list[ClusterInfo]:
        return []

    def get_collections(self) -> list[MongoCollectionInfo]:
        return []

    def get_indices(self, *, include_field_caps: bool = False) -> list[ElasticsearchIndexInfo]:
        return []

    def get_data_streams(self) -> list[ElasticsearchDataStreamInfo]:
        return []

    def get_component_templates(self) -> list[ElasticsearchComponentTemplateInfo]:
        return []

    def get_ingest_pipelines(self) -> list[ElasticsearchPipelineInfo]:
        return []

    def get_index_templates(self) -> list[ElasticsearchIndexTemplateInfo]:
        return []

    def get_ilm_policies(self) -> list[ElasticsearchIlmPolicyInfo]:
        return []

    def get_slm_policies(self) -> list[ElasticsearchSlmPolicyInfo]:
        return []

    def get_slm_export_diagnostics(self) -> str | None:
        return None

    def get_snapshot_repositories(self) -> list[ElasticsearchSnapshotRepositoryInfo]:
        return []

    def get_search_templates(self) -> list[ElasticsearchSearchTemplateInfo]:
        return []

    def get_search_template_export_diagnostics(self) -> str | None:
        return None

    def list_schemas(self) -> list[str]:
        return []

    def get_synonyms(self) -> list[SynonymInfo]:
        return []

    def get_dependencies(self) -> list[DependencyEdge]:
        return []

    def limits(self) -> dict[str, Any]:
        return {}
