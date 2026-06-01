from __future__ import annotations

from md_generator.db.core.elasticsearch_markdown import (
    format_opensearch_compatibility_markdown,
    format_search_architecture_markdown,
)
from md_generator.db.core.elasticsearch_query_classify import (
    HYBRID_SEARCH,
    FULL_TEXT,
    VECTOR_SEARCH,
)
from md_generator.db.core.elasticsearch_synthesis import (
    CompatibilityProbes,
    ElasticsearchExportContext,
    MappingAggregateMetrics,
    QueryTypeSummary,
    aggregate_mapping_metrics,
    aggregate_query_type_summary,
    build_compatibility_probes,
    should_show_opensearch_matrix,
)
from md_generator.db.core.models import ElasticsearchIndexInfo


def test_format_search_architecture_markdown() -> None:
    ctx = ElasticsearchExportContext(
        cluster_name="prod",
        index_pattern="logs-*",
        alias_map={"logs-current": ["logs-2025.05.01", "logs-2025.05.02"]},
        indices=["logs-2025.05.01"],
        data_streams=[("logs", "logs-template", (".ds-logs-000001",))],
        component_templates=["logs-mappings"],
        index_templates=[("logs", ("logs-*",), ("logs-mappings",), False)],
        pipelines=["ingest-logs"],
        ilm_policies=[("30-days", "ilm")],
    )
    md = format_search_architecture_markdown(ctx)
    assert "# Search architecture" in md
    assert "`prod`" in md
    assert "## Ingestion" in md
    assert "## Indexing" in md
    assert "## Retention" in md
    assert "## Alias routing" in md
    assert "alias_graph.md" in md
    assert "`logs-current`" in md


def test_format_search_architecture_lifecycle_and_vector_readiness() -> None:
    ctx = ElasticsearchExportContext(
        cluster_name="ai-cluster",
        mapping_aggregate=MappingAggregateMetrics(
            total_fields=120,
            dense_vector_fields=12,
            semantic_text_fields=2,
            indices_with_vectors=["docs-v1", "docs-v2"],
            index_count=2,
        ),
        query_type_summary=QueryTypeSummary(
            counts={HYBRID_SEARCH: 3, VECTOR_SEARCH: 5, FULL_TEXT: 10},
            template_count=15,
        ),
        search_templates=["hybrid-search", "knn-query"],
        search_template_types=[
            ("hybrid-search", (HYBRID_SEARCH, FULL_TEXT, VECTOR_SEARCH)),
            ("knn-query", (VECTOR_SEARCH,)),
        ],
        snapshot_repositories=[("s3-backup", "s3")],
        slm_policies=[("daily", "s3-backup")],
    )
    md = format_search_architecture_markdown(ctx)
    assert "## Indexing" in md
    assert "### Mapping summary (aggregate)" in md
    assert "**Total mapped fields:** 120" in md
    assert "**Dense vector fields:** 12" in md
    assert "## Search" in md
    assert "### Query type summary" in md
    assert "Hybrid search" in md
    assert "## Backup" in md
    assert "## Vector / AI readiness" in md
    assert "Hybrid search likely" in md
    assert "`docs-v1`" in md


def test_aggregate_mapping_metrics_from_indices() -> None:
    indices = [
        ElasticsearchIndexInfo(
            name="a",
            aliases=(),
            mappings={"properties": {"v": {"type": "dense_vector"}}},
            settings={},
            shard_config={},
        ),
        ElasticsearchIndexInfo(
            name="b",
            aliases=(),
            mappings={"properties": {"t": {"type": "text"}}},
            settings={},
            shard_config={},
        ),
    ]
    agg = aggregate_mapping_metrics(indices)
    assert agg.index_count == 2
    assert agg.total_fields == 2
    assert agg.dense_vector_fields == 1
    assert agg.indices_with_vectors == ["a"]


def test_aggregate_query_type_summary() -> None:
    summary = aggregate_query_type_summary(
        [
            ("t1", (HYBRID_SEARCH, FULL_TEXT)),
            ("t2", (VECTOR_SEARCH,)),
        ]
    )
    assert summary.template_count == 2
    assert summary.counts[HYBRID_SEARCH] == 1
    assert summary.counts[FULL_TEXT] == 1
    assert summary.counts[VECTOR_SEARCH] == 1


def test_build_compatibility_probes_opensearch_mode() -> None:
    ctx = ElasticsearchExportContext(
        ilm_policies=[("p", "ism")],
        slm_policies=[("daily", "repo")],
        search_templates=["q"],
        snapshot_repositories=[("repo", "fs")],
    )
    probes = build_compatibility_probes(
        opensearch_mode=True,
        feats=frozenset(
            {
                "elasticsearch_ilm_policies",
                "elasticsearch_slm_policies",
                "elasticsearch_search_templates",
                "elasticsearch_snapshot_repositories",
            }
        ),
        ctx=ctx,
    )
    assert probes.opensearch_mode is True
    assert probes.ilm_source == "ism"
    assert probes.slm_available is True
    assert should_show_opensearch_matrix(probes) is True


def test_opensearch_matrix_when_slm_unavailable() -> None:
    probes = CompatibilityProbes(
        opensearch_mode=False,
        slm_enabled=True,
        slm_available=False,
        slm_diagnostics="slm.get_lifecycle failed: 404",
    )
    assert should_show_opensearch_matrix(probes) is True
    md = format_opensearch_compatibility_markdown(probes)
    assert "## OpenSearch Compatibility" in md
    assert "Unavailable (probe failed)" in md
    assert "slm.get_lifecycle failed" in md


def test_opensearch_matrix_hidden_when_no_signals() -> None:
    probes = CompatibilityProbes(
        opensearch_mode=False,
        ilm_enabled=True,
        ilm_source="ilm",
        slm_enabled=True,
        slm_available=True,
        search_templates_enabled=True,
        search_templates_exported=True,
    )
    assert should_show_opensearch_matrix(probes) is False
