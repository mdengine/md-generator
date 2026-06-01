from __future__ import annotations

from md_generator.db.core.elasticsearch_markdown import (
    format_elasticsearch_data_stream_markdown,
    format_elasticsearch_ilm_markdown,
    format_elasticsearch_index_markdown,
    format_elasticsearch_index_template_markdown,
    format_elasticsearch_pipeline_markdown,
    format_elasticsearch_search_template_markdown,
    format_elasticsearch_security_placeholder_markdown,
    format_elasticsearch_slm_markdown,
    format_elasticsearch_snapshot_repository_markdown,
)
from md_generator.db.core.elasticsearch_output import ElasticsearchOutputConfig
from md_generator.db.core.models import (
    ElasticsearchDataStreamInfo,
    ElasticsearchIlmPolicyInfo,
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSlmPolicyInfo,
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


def test_format_index_json_truncation_warning() -> None:
    huge_props = {f"f{i}": {"type": "keyword", "meta": "x" * 200} for i in range(300)}
    idx = ElasticsearchIndexInfo(
        name="big",
        aliases=(),
        mappings={"properties": huge_props},
        settings={},
        shard_config={},
    )
    warnings: list[str] = []
    md = format_elasticsearch_index_markdown(
        idx,
        output=ElasticsearchOutputConfig(
            mapping_mode="raw",
            max_json_block_chars=2000,
        ),
        warnings=warnings,
    )
    assert "## Export Warnings" in md
    assert any("truncated" in w.lower() for w in warnings)


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
            definition={"lang": "mustache", "source": {"query": {"match_all": {}}}},
            param_keys=("size",),
            source_length=12000,
            source_preview='{"query": {}}',
            source_truncated=True,
            query_types=("FULL_TEXT",),
        ),
    )
    assert "## Summary" in md
    assert "## Query type" in md
    assert "Full text" in md
    assert "12,000" in md
    assert "`size`" in md
    assert "## Query body" in md
    assert "truncated" in md.lower()


def test_format_index_mapping_summary_and_operational_notes() -> None:
    idx = ElasticsearchIndexInfo(
        name="vector-index",
        aliases=(),
        mappings={
            "dynamic": "strict",
            "properties": {
                "embedding": {"type": "dense_vector", "dims": 768},
                "items": {"type": "nested", "properties": {"sku": {"type": "keyword"}}},
            },
        },
        settings={},
        shard_config={},
        health="yellow",
        replica_shards=0,
    )
    md = format_elasticsearch_index_markdown(
        idx,
        output=ElasticsearchOutputConfig(mapping_mode="flattened", include_raw_json=False),
    )
    assert "## Mapping Summary" in md
    assert "**Total fields:** 3" in md
    assert "**Nested fields:** 1" in md
    assert "**Dense vector fields:** 1" in md
    assert "**Dynamic mappings:** `strict`" in md
    assert "## Operational Notes" in md
    assert "`yellow`" in md
    assert "No replica shards" in md
    assert "dense_vector" in md


def test_format_ilm_slm_and_data_stream_operational_notes() -> None:
    ilm_md = format_elasticsearch_ilm_markdown(
        ElasticsearchIlmPolicyInfo(
            "30d",
            {
                "phases": {
                    "cold": {"actions": {"searchable_snapshot": {}}},
                    "delete": {"actions": {"delete": {}}},
                }
            },
        ),
    )
    assert "## Operational Notes" in ilm_md
    assert "cold" in ilm_md
    assert "Delete action" in ilm_md
    assert "Snapshot action" in ilm_md

    slm_md = format_elasticsearch_slm_markdown(
        ElasticsearchSlmPolicyInfo(
            name="daily",
            policy={"retention": {"expire_after": "30d"}},
            schedule="0 0 * * *",
            repository="s3-repo",
        ),
    )
    assert "## Operational Notes" in slm_md
    assert "Scheduled snapshots" in slm_md
    assert "Retention expire_after" in slm_md

    ds_md = format_elasticsearch_data_stream_markdown(
        ElasticsearchDataStreamInfo(
            name="logs",
            indices=(".ds-logs-000001",),
            template="logs-template",
            generation=2,
            definition={"data_streams": {}},
        ),
    )
    assert "## Operational Notes" in ds_md
    assert "generation: 2" in ds_md.lower()
    assert "logs-template" in ds_md


def test_format_snapshot_and_search_template_operational_notes() -> None:
    snap_md = format_elasticsearch_snapshot_repository_markdown(
        ElasticsearchSnapshotRepositoryInfo(
            name="snap",
            repository_type="s3",
            operational={"readonly": True, "compress": True},
            settings={},
            notes="SLM policies: daily",
        ),
    )
    assert "## Operational Notes" in snap_md
    assert "read-only" in snap_md.lower()
    assert "compression" in snap_md.lower()
    assert "SLM snapshot policies" in snap_md

    hybrid_md = format_elasticsearch_search_template_markdown(
        ElasticsearchSearchTemplateInfo(
            name="hybrid",
            lang="mustache",
            definition={},
            query_types=("HYBRID_SEARCH", "FULL_TEXT", "VECTOR_SEARCH"),
        ),
    )
    assert "## Operational Notes" in hybrid_md
    assert "Hybrid lexical + vector" in hybrid_md


def test_format_security_placeholder_markdown() -> None:
    md = format_elasticsearch_security_placeholder_markdown(
        feature="elasticsearch_security_roles",
        title="Elasticsearch security roles",
    )
    assert "intentional non-export" in md
    assert "elasticsearch_security_roles" in md
    assert "no live cluster security apis are called" in md.lower()
