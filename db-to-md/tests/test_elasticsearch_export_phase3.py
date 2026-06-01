from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from md_generator.db.core.elasticsearch_export import export_elasticsearch_markdown
from md_generator.db.core.models import (
    ElasticsearchIlmPolicyInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSnapshotRepositoryInfo,
)
from md_generator.db.core.run_config import RunConfig


def test_export_phase3_features(tmp_path: Path) -> None:
    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.cluster_name = "es-test"
    adapter.get_indices.return_value = []
    adapter.get_data_streams.return_value = []
    adapter.get_component_templates.return_value = []
    adapter.get_index_templates.return_value = [
        ElasticsearchIndexTemplateInfo(
            name="tpl",
            index_patterns=("x-*",),
            priority=1,
            template={},
        )
    ]
    adapter.get_ingest_pipelines.return_value = [
        ElasticsearchPipelineInfo("pipe", {"processors": []}),
    ]
    adapter.get_ilm_policies.return_value = [
        ElasticsearchIlmPolicyInfo("pol", {"phases": {}}, source="ilm"),
    ]

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset(
            {
                "elasticsearch_index_templates",
                "elasticsearch_ingest_pipelines",
                "elasticsearch_ilm_policies",
            }
        ),
        write_manifest=False,
    )
    root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
    assert (root / "elasticsearch" / "templates" / "tpl.md").is_file()
    assert (root / "elasticsearch" / "pipelines" / "pipe.md").is_file()
    assert (root / "elasticsearch" / "ilm" / "pol.md").is_file()


def test_export_slm_policies(tmp_path: Path) -> None:
    from md_generator.db.core.models import ElasticsearchSlmPolicyInfo

    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.get_slm_policies.return_value = [
        ElasticsearchSlmPolicyInfo(
            name="daily",
            policy={"schedule": "0 0 * * *", "repository": "backup"},
            schedule="0 0 * * *",
            repository="backup",
        ),
    ]
    adapter.get_slm_export_diagnostics.return_value = None

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset({"elasticsearch_slm_policies"}),
        write_manifest=False,
    )
    root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
    slm_md = root / "elasticsearch" / "slm" / "daily.md"
    assert slm_md.is_file()
    text = slm_md.read_text(encoding="utf-8")
    assert "SLM policy" in text
    assert "`backup`" in text


def test_export_snapshots_search_templates_and_security_placeholders(tmp_path: Path) -> None:
    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.cluster_name = "es-test"
    adapter.get_snapshot_repositories.return_value = [
        ElasticsearchSnapshotRepositoryInfo(
            name="repo",
            repository_type="fs",
            operational={"location": "/backup"},
            settings={},
        ),
    ]
    adapter.get_search_templates.return_value = [
        ElasticsearchSearchTemplateInfo(
            name="tpl",
            lang="mustache",
            definition={"lang": "mustache", "source": "{}"},
            source_preview="{}",
            source_length=2,
        ),
    ]
    adapter.get_search_template_export_diagnostics.return_value = None

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset(
            {
                "elasticsearch_snapshot_repositories",
                "elasticsearch_search_templates",
                "elasticsearch_security_roles",
                "elasticsearch_security_api_keys",
            }
        ),
        write_manifest=False,
    )
    root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
    assert (root / "elasticsearch" / "snapshots" / "repo.md").is_file()
    assert (root / "elasticsearch" / "search_templates" / "tpl.md").is_file()
    assert (root / "elasticsearch" / "security" / "roles.md").is_file()
    assert (root / "elasticsearch" / "security" / "api_keys.md").is_file()
    roles = (root / "elasticsearch" / "security" / "roles.md").read_text(encoding="utf-8")
    assert "intentional non-export" in roles


def test_export_search_template_diagnostics_file(tmp_path: Path) -> None:
    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.get_search_templates.return_value = []
    adapter.get_search_template_export_diagnostics.return_value = "GET /_scripts failed: forbidden"

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset({"elasticsearch_search_templates"}),
        write_manifest=False,
    )
    root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
    diag = root / "elasticsearch" / "search_templates" / "_diagnostics.md"
    assert diag.is_file()
    assert "forbidden" in diag.read_text(encoding="utf-8")
