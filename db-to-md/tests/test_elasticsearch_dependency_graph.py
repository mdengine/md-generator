from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from md_generator.db.core.elasticsearch_dependency_graph import (
    build_template_dependency_rows,
    format_search_dependency_graph_markdown,
    should_emit_dependency_graph,
)
from md_generator.db.core.elasticsearch_export import export_elasticsearch_markdown
from md_generator.db.core.elasticsearch_synthesis import ElasticsearchExportContext
from md_generator.db.core.models import (
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchSearchTemplateInfo,
)
from md_generator.db.core.run_config import RunConfig


def test_build_template_dependency_rows_explicit_and_inferred() -> None:
    ctx = ElasticsearchExportContext(
        indices=["logs-2025.05.01", "metrics-2025.05.01"],
        alias_map={"logs-current": ["logs-2025.05.01"]},
        pipelines=["ingest-logs"],
    )
    templates = [
        ElasticsearchSearchTemplateInfo(
            name="search-logs",
            lang="mustache",
            definition={
                "lang": "mustache",
                "source": {
                    "query": {"term": {"x": "y"}},
                    "index": "logs-current",
                },
            },
            query_types=("FULL_TEXT",),
        ),
        ElasticsearchSearchTemplateInfo(
            name="search-metrics",
            lang="mustache",
            definition={
                "lang": "mustache",
                "source": '{"query": {}, "index": "metrics-*"}',
            },
            query_types=("FULL_TEXT",),
        ),
    ]
    rows = build_template_dependency_rows(templates, ctx)
    by_name = {r.template_name: r for r in rows}
    assert ("logs-current", "explicit") in by_name["search-logs"].aliases
    assert by_name["search-logs"].confidence == "explicit"
    assert any(idx == "metrics-2025.05.01" for idx, _ in by_name["search-metrics"].indices)


def test_build_template_dependency_rows_uses_index_template_pipelines() -> None:
    ctx = ElasticsearchExportContext(indices=["logs-2025.05.01"])
    templates = [
        ElasticsearchSearchTemplateInfo(
            name="tpl",
            lang="mustache",
            definition={
                "lang": "mustache",
                "source": {"query": {"match_all": {}}, "index": "logs-*"},
            },
        ),
    ]
    index_templates = [
        ElasticsearchIndexTemplateInfo(
            name="logs",
            index_patterns=("logs-*",),
            priority=1,
            template={"settings": {"index": {"default_pipeline": "ingest-logs"}}},
        ),
    ]
    rows = build_template_dependency_rows(templates, ctx, index_templates)
    assert ("logs-2025.05.01", "inferred") in rows[0].indices


def test_format_search_dependency_graph_markdown_includes_disclaimer() -> None:
    ctx = ElasticsearchExportContext(indices=["logs-2025.05.01"])
    templates = [
        ElasticsearchSearchTemplateInfo(
            name="t",
            lang="mustache",
            definition={"lang": "mustache", "source": {"index": "logs-2025.05.01"}},
            query_types=("FULL_TEXT",),
        ),
    ]
    md = format_search_dependency_graph_markdown(
        build_template_dependency_rows(templates, ctx),
        index_pattern="logs-*",
    )
    assert "Heuristic map only" in md
    assert "| Template | Likely indices |" in md
    assert "`t`" in md


def test_should_emit_dependency_graph_feature_and_limit() -> None:
    feats = frozenset({"elasticsearch_search_dependency_graph"})
    assert should_emit_dependency_graph(feats, {}) is True
    feats2 = frozenset({"elasticsearch_search_architecture"})
    assert should_emit_dependency_graph(feats2, {"emit_dependency_graph": True}) is True
    assert should_emit_dependency_graph(feats2, {}) is False


def test_export_dependency_graph_file(tmp_path: Path) -> None:
    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.get_indices.return_value = [
        ElasticsearchIndexInfo(
            name="logs-2025.05.01",
            aliases=(),
            mappings={},
            settings={},
            shard_config={},
            health="green",
            doc_count=1,
            store_size="1kb",
            primary_shards=1,
            replica_shards=0,
        ),
    ]
    adapter.get_search_templates.return_value = [
        ElasticsearchSearchTemplateInfo(
            name="search-logs",
            lang="mustache",
            definition={
                "lang": "mustache",
                "source": {"query": {"match_all": {}}, "index": "logs-2025.05.01"},
            },
            query_types=("FULL_TEXT",),
        ),
    ]

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset(
            {
                "elasticsearch_indices",
                "elasticsearch_search_templates",
                "elasticsearch_search_dependency_graph",
            }
        ),
        write_manifest=False,
    )
    root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
    dep = root / "elasticsearch" / "search_dependency_graph.md"
    assert dep.is_file()
    text = dep.read_text(encoding="utf-8")
    assert "search-logs" in text
    assert "logs-2025.05.01" in text
