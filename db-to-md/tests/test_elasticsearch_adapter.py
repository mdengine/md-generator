from __future__ import annotations

from unittest.mock import MagicMock, patch

from md_generator.db.adapters.elasticsearch_adapter import ElasticsearchAdapter


def test_get_indices_from_mock_client() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {"index_pattern": "logs-*"})
    mock_client = MagicMock()
    mock_client.cat.indices.return_value = [
        {
            "index": "logs-2025",
            "health": "green",
            "docs.count": "10",
            "store.size": "1kb",
            "pri": "1",
            "rep": "1",
        }
    ]
    mock_client.indices.get_mapping.return_value = {
        "logs-2025": {"mappings": {"properties": {"msg": {"type": "text"}}}}
    }
    mock_client.indices.get_settings.return_value = {
        "logs-2025": {"settings": {"index": {"number_of_shards": "1"}}}
    }
    mock_client.indices.get_alias.return_value = {
        "logs-2025": {"aliases": {"logs-alias": {}}}
    }

    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        indices = adapter.get_indices()

    assert len(indices) == 1
    assert indices[0].name == "logs-2025"
    assert indices[0].aliases == ("logs-alias",)
    assert indices[0].doc_count == 10
    assert "msg" in str(indices[0].mappings)


def test_get_data_streams_mock() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.indices.get_data_stream.return_value = {
        "data_streams": [
            {
                "name": "logs",
                "template": "logs-template",
                "indices": [{"index_name": ".ds-logs-000001"}],
            }
        ]
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        streams = adapter.get_data_streams()
    assert len(streams) == 1
    assert streams[0].name == "logs"
    assert streams[0].template == "logs-template"


def test_get_component_templates_mock() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.cluster.get_component_template.return_value = {
        "component_templates": [
            {"name": "logs-mappings", "component_template": {"template": {"mappings": {}}}}
        ]
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        templates = adapter.get_component_templates()
    assert len(templates) == 1
    assert templates[0].name == "logs-mappings"


def test_get_ingest_pipelines_mock() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.ingest.get_pipeline.return_value = {
        "my-pipeline": {"description": "test", "processors": []},
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        pipelines = adapter.get_ingest_pipelines()
    assert len(pipelines) == 1
    assert pipelines[0].name == "my-pipeline"


def test_get_index_templates_composable_and_legacy() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.indices.get_index_template.return_value = {
        "index_templates": [
            {
                "name": "logs",
                "index_template": {
                    "index_patterns": ["logs-*"],
                    "template": {"settings": {}},
                    "composed_of": ["logs-mappings"],
                    "priority": 100,
                },
            }
        ]
    }
    mock_client.indices.get_template.return_value = {
        "legacy-logs": {"index_patterns": ["legacy-*"], "order": 1, "settings": {}},
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        templates = adapter.get_index_templates()
    names = {t.name for t in templates}
    assert "logs" in names
    assert "legacy-logs" in names
    logs = next(t for t in templates if t.name == "logs")
    assert logs.composed_of == ("logs-mappings",)
    legacy = next(t for t in templates if t.name == "legacy-logs")
    assert legacy.legacy is True


def test_get_ilm_policies_ilm_mock() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.ilm.get_lifecycle.return_value = {
        "30-days": {"policy": {"phases": {"hot": {"actions": {}}}}},
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        policies = adapter.get_ilm_policies()
    assert len(policies) == 1
    assert policies[0].name == "30-days"
    assert policies[0].source == "ilm"


def test_get_indices_field_caps_per_index() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.cat.indices.return_value = [{"index": "idx-a", "health": "green"}]
    mock_client.indices.get_mapping.return_value = {"idx-a": {"mappings": {}}}
    mock_client.indices.get_settings.return_value = {"idx-a": {"settings": {}}}
    mock_client.indices.get_alias.return_value = {}
    mock_client.field_caps.return_value = {
        "fields": {"f": {"keyword": {"type": "keyword", "searchable": True}}},
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        indices = adapter.get_indices(include_field_caps=True)
    assert indices[0].field_caps is not None
    assert "fields" in indices[0].field_caps
    mock_client.field_caps.assert_called_once_with(index="idx-a", fields="*")


def test_get_snapshot_repositories_mock() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.snapshot.get_repository.return_value = {
        "backup": {
            "type": "fs",
            "settings": {"location": "/backup", "compress": True, "extra": "x"},
        },
    }
    mock_client.slm.get_lifecycle.side_effect = Exception("no slm")
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        repos = adapter.get_snapshot_repositories()
    assert len(repos) == 1
    assert repos[0].name == "backup"
    assert repos[0].repository_type == "fs"
    assert repos[0].operational["location"] == "/backup"
    assert repos[0].operational["compress"] is True
    assert repos[0].settings["extra"] == "x"


def test_get_snapshot_repositories_type_filter() -> None:
    adapter = ElasticsearchAdapter(
        "https://localhost:9200",
        {"snapshot_repository_types": "s3"},
    )
    mock_client = MagicMock()
    mock_client.snapshot.get_repository.return_value = {
        "fs": {"type": "fs", "settings": {"location": "/x"}},
        "s3": {"type": "s3", "settings": {"bucket": "b"}},
    }
    mock_client.slm.get_lifecycle.side_effect = Exception("no slm")
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        repos = adapter.get_snapshot_repositories()
    assert [r.name for r in repos] == ["s3"]


def test_get_search_templates_mustache_only() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.transport.perform_request.return_value = {
        "search-tpl": {"lang": "mustache", "source": {"query": {}}},
        "painless-script": {"lang": "painless", "source": "return 1"},
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        templates = adapter.get_search_templates()
    assert len(templates) == 1
    assert templates[0].name == "search-tpl"
    assert templates[0].source_preview is not None


def test_get_search_templates_nested_script_source() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.transport.perform_request.return_value = {
        "tpl": {
            "lang": "mustache",
            "script": {"source": '{"query": {"term": {"x": "{{v}}"}}}', "params": {"v": "a"}},
        },
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        templates = adapter.get_search_templates()
    assert len(templates) == 1
    assert templates[0].param_keys == ("v",)


def test_get_search_templates_diagnostics_on_total_failure() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {})
    mock_client = MagicMock()
    mock_client.transport.perform_request.side_effect = Exception("forbidden")
    mock_client.cluster.state.side_effect = Exception("also forbidden")
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        templates = adapter.get_search_templates()
    assert templates == []
    assert adapter.get_search_template_export_diagnostics() is not None
    assert "forbidden" in adapter.get_search_template_export_diagnostics()


def test_get_ilm_policies_opensearch_ism() -> None:
    adapter = ElasticsearchAdapter("https://localhost:9200", {"opensearch": True})
    mock_client = MagicMock()
    mock_client.transport.perform_request.return_value = {
        "policies": [
            {"_id": "rollover", "_source": {"policy": {"description": "rollover policy"}}},
        ]
    }
    with patch.object(adapter, "_ensure_client", return_value=mock_client):
        policies = adapter.get_ilm_policies()
    assert len(policies) == 1
    assert policies[0].name == "rollover"
    assert policies[0].source == "ism"
    mock_client.ilm.get_lifecycle.assert_not_called()
