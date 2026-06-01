from __future__ import annotations

from md_generator.db.core.elasticsearch_markdown import format_search_architecture_markdown
from md_generator.db.core.elasticsearch_synthesis import ElasticsearchExportContext


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
    assert "Data streams" in md
    assert "alias_graph.md" in md
    assert "`logs-current`" in md
