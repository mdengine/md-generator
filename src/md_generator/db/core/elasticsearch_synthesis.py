"""Collected metadata for ``search_architecture.md`` synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field

from md_generator.db.core.elasticsearch_operational_notes import mapping_complexity_metrics
from md_generator.db.core.elasticsearch_query_classify import (
    HYBRID_SEARCH,
    SEMANTIC_SEARCH,
    VECTOR_SEARCH,
)
from md_generator.db.core.models import ElasticsearchIndexInfo, ElasticsearchSearchTemplateInfo


@dataclass
class MappingAggregateMetrics:
    total_fields: int = 0
    nested_fields: int = 0
    dense_vector_fields: int = 0
    sparse_vector_fields: int = 0
    semantic_text_fields: int = 0
    indices_with_vectors: list[str] = field(default_factory=list)
    index_count: int = 0


@dataclass
class QueryTypeSummary:
    counts: dict[str, int] = field(default_factory=dict)
    template_count: int = 0


@dataclass
class CompatibilityProbes:
    opensearch_mode: bool = False
    ilm_enabled: bool = False
    ilm_source: str | None = None
    ilm_policy_count: int = 0
    slm_enabled: bool = False
    slm_available: bool | None = None
    slm_diagnostics: str | None = None
    slm_policy_count: int = 0
    search_templates_enabled: bool = False
    search_templates_exported: bool | None = None
    search_templates_diagnostics: str | None = None
    search_template_count: int = 0
    snapshot_repositories_enabled: bool = False
    snapshot_repository_count: int = 0
    security_export: str = "placeholder_only"


@dataclass
class ElasticsearchExportContext:
    cluster_name: str | None = None
    index_pattern: str = "*"
    alias_map: dict[str, list[str]] = field(default_factory=dict)
    indices: list[str] = field(default_factory=list)
    data_streams: list[tuple[str, str | None, tuple[str, ...]]] = field(default_factory=list)
    component_templates: list[str] = field(default_factory=list)
    index_templates: list[tuple[str, tuple[str, ...], tuple[str, ...] | None, bool]] = field(
        default_factory=list
    )
    pipelines: list[str] = field(default_factory=list)
    ilm_policies: list[tuple[str, str]] = field(default_factory=list)
    slm_policies: list[tuple[str, str | None]] = field(default_factory=list)
    snapshot_repositories: list[tuple[str, str]] = field(default_factory=list)
    search_templates: list[str] = field(default_factory=list)
    search_template_types: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)
    search_template_entities: list[ElasticsearchSearchTemplateInfo] = field(default_factory=list)
    mapping_aggregate: MappingAggregateMetrics | None = None
    query_type_summary: QueryTypeSummary | None = None
    compatibility: CompatibilityProbes | None = None


def aggregate_mapping_metrics(indices: list[ElasticsearchIndexInfo]) -> MappingAggregateMetrics:
    agg = MappingAggregateMetrics(index_count=len(indices))
    for idx in indices:
        mappings_root = idx.mappings if isinstance(idx.mappings, dict) else None
        if mappings_root is None:
            continue
        props = mappings_root.get("properties")
        if props is None:
            props = mappings_root
        if not isinstance(props, dict):
            continue
        metrics = mapping_complexity_metrics(
            props,
            mappings_root=mappings_root,
        )
        agg.total_fields += int(metrics.get("total_fields") or 0)
        agg.nested_fields += int(metrics.get("nested_fields") or 0)
        agg.dense_vector_fields += int(metrics.get("dense_vector_fields") or 0)
        agg.sparse_vector_fields += int(metrics.get("sparse_vector_fields") or 0)
        agg.semantic_text_fields += int(metrics.get("semantic_text_fields") or 0)
        vector_total = (
            int(metrics.get("dense_vector_fields") or 0)
            + int(metrics.get("sparse_vector_fields") or 0)
            + int(metrics.get("semantic_text_fields") or 0)
        )
        if vector_total:
            agg.indices_with_vectors.append(idx.name)
    return agg


def aggregate_query_type_summary(
    template_types: list[tuple[str, tuple[str, ...]]],
) -> QueryTypeSummary:
    summary = QueryTypeSummary(template_count=len(template_types))
    for _, types in template_types:
        for qt in types:
            summary.counts[qt] = summary.counts.get(qt, 0) + 1
    return summary


def build_compatibility_probes(
    *,
    opensearch_mode: bool,
    feats: frozenset[str],
    ctx: ElasticsearchExportContext,
    slm_diagnostics: str | None = None,
    search_template_diagnostics: str | None = None,
) -> CompatibilityProbes:
    probes = CompatibilityProbes(opensearch_mode=opensearch_mode)

    if "elasticsearch_ilm_policies" in feats:
        probes.ilm_enabled = True
        probes.ilm_policy_count = len(ctx.ilm_policies)
        if ctx.ilm_policies:
            sources = {source for _, source in ctx.ilm_policies}
            if opensearch_mode or sources == {"ism"} or (sources & {"ism"}):
                probes.ilm_source = "ism"
            else:
                probes.ilm_source = "ilm"

    if "elasticsearch_slm_policies" in feats:
        probes.slm_enabled = True
        probes.slm_policy_count = len(ctx.slm_policies)
        probes.slm_diagnostics = slm_diagnostics
        if slm_diagnostics:
            probes.slm_available = False
        else:
            probes.slm_available = True

    if "elasticsearch_search_templates" in feats:
        probes.search_templates_enabled = True
        probes.search_template_count = len(ctx.search_templates)
        probes.search_templates_diagnostics = search_template_diagnostics
        if search_template_diagnostics and not ctx.search_templates:
            probes.search_templates_exported = False
        elif ctx.search_templates:
            probes.search_templates_exported = True
        elif search_template_diagnostics:
            probes.search_templates_exported = False
        else:
            probes.search_templates_exported = True

    if "elasticsearch_snapshot_repositories" in feats:
        probes.snapshot_repositories_enabled = True
        probes.snapshot_repository_count = len(ctx.snapshot_repositories)

    return probes


def should_show_opensearch_matrix(probes: CompatibilityProbes) -> bool:
    if probes.opensearch_mode:
        return True
    if probes.ilm_source == "ism" and not probes.opensearch_mode:
        return True
    if probes.slm_available is False:
        return True
    if probes.search_templates_exported is False:
        return True
    if probes.search_templates_diagnostics:
        return True
    return False


def _ilm_export_status(probes: CompatibilityProbes) -> str:
    if not probes.ilm_enabled:
        return "Not exported"
    if probes.opensearch_mode or probes.ilm_source == "ism":
        return "ISM fallback (OpenSearch mode)" if probes.opensearch_mode else "ISM fallback"
    if probes.ilm_policy_count:
        return f"Exported ({probes.ilm_policy_count} policies)"
    return "Exported (no policies returned)"


def _slm_export_status(probes: CompatibilityProbes) -> str:
    if not probes.slm_enabled:
        return "Not exported"
    if probes.slm_available is False:
        return "Unavailable (probe failed)"
    if probes.slm_policy_count:
        return f"Available ({probes.slm_policy_count} policies)"
    return "Available (no policies returned)"


def _search_template_export_status(probes: CompatibilityProbes) -> str:
    if not probes.search_templates_enabled:
        return "Not exported"
    if probes.search_templates_exported is False:
        return "Restricted / unavailable"
    if probes.search_template_count:
        return f"Exported ({probes.search_template_count} templates)"
    if probes.search_templates_diagnostics:
        return "Partial / restricted"
    return "Exported (no templates returned)"


def _snapshot_export_status(probes: CompatibilityProbes) -> str:
    if not probes.snapshot_repositories_enabled:
        return "Not exported"
    if probes.snapshot_repository_count:
        return f"Exported ({probes.snapshot_repository_count} repositories)"
    return "Exported (no repositories returned)"


def compatibility_matrix_rows(probes: CompatibilityProbes) -> list[tuple[str, str, str]]:
    return [
        ("ILM policies", "Native ILM", _ilm_export_status(probes)),
        ("SLM policies", "Native SLM", _slm_export_status(probes)),
        ("Search templates", "Stored scripts", _search_template_export_status(probes)),
        ("Security export", "Live APIs", "Placeholder only"),
        ("Snapshot repositories", "Native", _snapshot_export_status(probes)),
    ]
