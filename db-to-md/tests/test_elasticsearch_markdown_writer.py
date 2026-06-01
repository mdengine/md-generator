from __future__ import annotations

from md_generator.db.core.elasticsearch_markdown import (
    format_elasticsearch_ilm_markdown,
    format_elasticsearch_index_markdown,
    format_elasticsearch_index_template_markdown,
    format_elasticsearch_pipeline_markdown,
    format_elasticsearch_search_template_markdown,
    format_elasticsearch_security_placeholder_markdown,
    format_elasticsearch_snapshot_repository_markdown,
)
from md_generator.db.core.elasticsearch_output import ElasticsearchOutputConfig
from md_generator.db.core.models import (
    ElasticsearchIlmPolicyInfo,
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSnapshotRepositoryInfo,
)


def test_format_index_flattened() -> None:
    idx = ElasticsearchIndexInfo(
        name="logs-2025",
        aliases=("logs-current",),
        mappings={"properties": {"message": {"type": "text"}, "@timestamp": {"type": "date"}}},
        settings={"index": {"number_of_shards": "3", "analysis": {"analyzer": {}}}},
        shard_config={"number_of_shards": "3", "number_of_replicas": "1"},
        health="green",
        doc_count=1000,
        store_size="1.2mb",
        primary_shards=3,
        replica_shards=1,
    )
    md = format_elasticsearch_index_markdown(
        idx,
        output=ElasticsearchOutputConfig(mapping_mode="flattened", include_raw_json=False),
    )
    assert "# Index: `logs-2025`" in md
    assert "`logs-current`" in md
    assert "| `message` | `text` | — |" in md
    assert "Shard configuration" in md
    assert "**Health:** `green`" in md


def test_format_index_raw_json_when_requested() -> None:
    idx = ElasticsearchIndexInfo(
        name="x",
        aliases=(),
        mappings={"properties": {"a": {"type": "keyword"}}},
        settings={},
        shard_config={},
    )
    md = format_elasticsearch_index_markdown(
        idx,
        output=ElasticsearchOutputConfig(mapping_mode="flattened", include_raw_json=True),
    )
    assert "Mappings (raw JSON)" in md
    assert '"keyword"' in md


def test_format_pipeline_and_template_and_ilm() -> None:
    pipe_md = format_elasticsearch_pipeline_markdown(
        ElasticsearchPipelineInfo("ingest-1", {"processors": []}),
    )
    assert "# Ingest pipeline: `ingest-1`" in pipe_md

    tpl_md = format_elasticsearch_index_template_markdown(
        ElasticsearchIndexTemplateInfo(
            name="logs",
            index_patterns=("logs-*",),
            priority=50,
            template={"settings": {}},
            composed_of=("base",),
        ),
    )
    assert "Composed of" in tpl_md
    assert "`logs-*`" in tpl_md

    ilm_md = format_elasticsearch_ilm_markdown(
        ElasticsearchIlmPolicyInfo("30d", {"phases": {}}, source="ism"),
    )
    assert "ISM (OpenSearch)" in ilm_md


def test_format_index_field_caps_table() -> None:
    idx = ElasticsearchIndexInfo(
        name="x",
        aliases=(),
        mappings={},
        settings={},
        shard_config={},
        field_caps={
            "fields": {
                "msg": {"text": {"type": "text", "searchable": True, "aggregatable": False}},
            }
        },
    )
    md = format_elasticsearch_index_markdown(
        idx,
        output=ElasticsearchOutputConfig(mapping_mode="flattened", include_raw_json=False),
    )
    assert "## Field capabilities" in md
    assert "| `msg` | `text` |" in md


def test_format_index_flattened_includes_attributes_column() -> None:
    idx = ElasticsearchIndexInfo(
        name="vector-index",
        aliases=(),
        mappings={
            "properties": {
                "embedding": {"type": "dense_vector", "dims": 768, "similarity": "cosine"},
                "rel": {"type": "join", "relations": {"q": "a"}},
            }
        },
        settings={},
        shard_config={},
    )
    md = format_elasticsearch_index_markdown(
        idx,
        output=ElasticsearchOutputConfig(mapping_mode="flattened", include_raw_json=False),
    )
    assert "| Field | Type | Attributes |" in md
    assert "dims=768" in md
    assert "relations=q->a" in md


def test_format_snapshot_repository_operational_table_and_json() -> None:
    md = format_elasticsearch_snapshot_repository_markdown(
        ElasticsearchSnapshotRepositoryInfo(
            name="snap",
            repository_type="s3",
            operational={"bucket": "b", "readonly": True},
            settings={"plugin_setting": "x"},
            notes="SLM policies: daily",
        ),
    )
    assert "## Operational settings" in md
    assert "`bucket`" in md
    assert "## Provider-specific settings" in md
    assert "## Full settings (JSON)" in md
    assert "SLM policies: daily" in md


def test_format_search_template_summary_and_truncation_note() -> None:
    md = format_elasticsearch_search_template_markdown(
        ElasticsearchSearchTemplateInfo(
            name="q",
            lang="mustache",
            definition={"lang": "mustache", "source": "x"},
            param_keys=("size",),
            source_length=12000,
            source_preview='{"query": {}}',
            source_truncated=True,
        ),
    )
    assert "## Summary" in md
    assert "12,000" in md
    assert "`size`" in md
    assert "## Query body" in md
    assert "truncated" in md.lower()


def test_format_security_placeholder_markdown() -> None:
    md = format_elasticsearch_security_placeholder_markdown(
        feature="elasticsearch_security_roles",
        title="Elasticsearch security roles",
    )
    assert "intentional non-export" in md
    assert "elasticsearch_security_roles" in md
    assert "no live cluster security apis are called" in md.lower()
