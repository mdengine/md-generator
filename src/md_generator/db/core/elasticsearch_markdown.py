"""Markdown formatters for Elasticsearch exports."""

from __future__ import annotations

import json
from typing import Any

from md_generator.db.core.elasticsearch_format import (
    analyzer_chain_lines,
    extract_analysis,
    field_caps_table_rows,
    flatten_mapping_properties,
    settings_without_analysis,
    summarize_mapping_properties,
)
from md_generator.db.core.elasticsearch_output import ElasticsearchOutputConfig
from md_generator.db.core.elasticsearch_synthesis import ElasticsearchExportContext
from md_generator.db.core.models import (
    ElasticsearchComponentTemplateInfo,
    ElasticsearchDataStreamInfo,
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchIlmPolicyInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSnapshotRepositoryInfo,
)


def _json_block(obj: Any) -> str:
    return "```json\n" + json.dumps(obj, sort_keys=True, indent=2) + "\n```\n\n"


def format_elasticsearch_index_markdown(
    idx: ElasticsearchIndexInfo,
    *,
    output: ElasticsearchOutputConfig,
) -> str:
    parts: list[str] = [f"# Index: `{idx.name}`\n\n"]

    stats: list[str] = []
    if idx.health:
        stats.append(f"**Health:** `{idx.health}`")
    if idx.doc_count is not None:
        stats.append(f"**Document count:** {idx.doc_count:,}")
    if idx.store_size:
        stats.append(f"**Store size:** `{idx.store_size}`")
    if idx.primary_shards is not None:
        stats.append(f"**Primary shards:** {idx.primary_shards}")
    if idx.replica_shards is not None:
        stats.append(f"**Replica shards:** {idx.replica_shards}")
    if stats:
        parts.append(" ".join(stats) + "\n\n")

    if idx.aliases:
        parts.append("**Aliases:** " + ", ".join(f"`{a}`" for a in idx.aliases) + "\n\n")
    else:
        parts.append("**Aliases:** _none_\n\n")

    if idx.shard_config:
        parts.append("## Shard configuration\n\n| Setting | Value |\n|---------|-------|\n")
        for k in sorted(idx.shard_config.keys()):
            parts.append(f"| `{k}` | `{idx.shard_config[k]}` |\n")
        parts.append("\n")

    props = idx.mappings.get("properties") if isinstance(idx.mappings, dict) else None
    if props is None and isinstance(idx.mappings, dict):
        props = idx.mappings

    mode = output.mapping_mode
    if isinstance(props, dict):
        if mode == "flattened":
            rows = flatten_mapping_properties(props)
            parts.append("## Field mappings\n\n| Field | Type | Attributes |\n|-------|------|------------|\n")
            for path, ftype, attrs in rows:
                parts.append(f"| `{path}` | `{ftype}` | {attrs or '—'} |\n")
            parts.append("\n")
        elif mode == "summarized":
            summary = summarize_mapping_properties(props)
            parts.append("## Field mappings (summary)\n\n")
            parts.append(f"- **Field count:** {summary['field_count']}\n")
            parts.append("- **Types:**\n\n")
            parts.append(_json_block(summary["types"]))
        elif mode == "raw":
            parts.append("## Mappings\n\n")
            parts.append(_json_block(idx.mappings))

        if output.include_raw_json and mode != "raw":
            parts.append("## Mappings (raw JSON)\n\n")
            parts.append(_json_block(idx.mappings))
    elif idx.mappings:
        parts.append("## Mappings\n\n")
        parts.append(_json_block(idx.mappings))

    analysis = extract_analysis(idx.settings)
    if analysis:
        af = output.analyzer_format
        if af in ("chain", "both"):
            chains = analyzer_chain_lines(analysis)
            if chains:
                parts.append("## Analyzer chains\n\n")
                for aname, chain in chains:
                    parts.append(f"- **`{aname}`:** `{chain}`\n")
                parts.append("\n")
        if af in ("json", "both"):
            parts.append("## Analyzers (JSON)\n\n")
            parts.append(_json_block(analysis))

    remaining = settings_without_analysis(idx.settings)
    if remaining:
        parts.append("## Settings\n\n")
        parts.append(_json_block(remaining))

    if idx.field_caps:
        rows = field_caps_table_rows(idx.field_caps)
        parts.append("## Field capabilities\n\n")
        if rows:
            parts.append("| Field | Type | Capabilities |\n|-------|------|-------------|\n")
            for field, ftype, caps in rows:
                parts.append(f"| `{field}` | `{ftype}` | {caps or '—'} |\n")
            parts.append("\n")
        elif not output.include_raw_json:
            parts.append("_No field capability rows returned._\n\n")
        if output.include_raw_json:
            parts.append("### Field capabilities (raw JSON)\n\n")
            parts.append(_json_block(idx.field_caps))

    return "".join(parts)


def format_elasticsearch_data_stream_markdown(ds: ElasticsearchDataStreamInfo) -> str:
    parts = [f"# Data stream: `{ds.name}`\n\n"]
    if ds.template:
        parts.append(f"**Index template:** `{ds.template}`\n\n")
    if ds.generation is not None:
        parts.append(f"**Generation:** {ds.generation}\n\n")
    if ds.indices:
        parts.append("**Backing indices:**\n\n")
        for ix in ds.indices:
            parts.append(f"- `{ix}`\n")
        parts.append("\n")
    parts.append("## Definition\n\n")
    parts.append(_json_block(ds.definition))
    return "".join(parts)


def format_elasticsearch_component_template_markdown(t: ElasticsearchComponentTemplateInfo) -> str:
    return (
        f"# Component template: `{t.name}`\n\n"
        "## Template\n\n"
        + _json_block(t.template)
    )


def format_elasticsearch_pipeline_markdown(p: ElasticsearchPipelineInfo) -> str:
    return f"# Ingest pipeline: `{p.name}`\n\n## Definition\n\n" + _json_block(p.definition)


def format_elasticsearch_index_template_markdown(t: ElasticsearchIndexTemplateInfo) -> str:
    parts = [f"# Index template: `{t.name}`\n\n"]
    if t.legacy:
        parts.append("_Legacy index template (`indices.get_template`)._\n\n")
    if t.index_patterns:
        parts.append(
            "**Index patterns:** "
            + ", ".join(f"`{p}`" for p in t.index_patterns)
            + "\n\n"
        )
    if t.priority is not None:
        parts.append(f"**Priority:** {t.priority}\n\n")
    if t.composed_of:
        parts.append(
            "**Composed of:** " + ", ".join(f"`{c}`" for c in t.composed_of) + "\n\n"
        )
    parts.append("## Template body\n\n")
    parts.append(_json_block(t.template))
    return "".join(parts)


def format_elasticsearch_ilm_markdown(pol: ElasticsearchIlmPolicyInfo) -> str:
    src = "ISM (OpenSearch)" if pol.source == "ism" else "ILM (Elasticsearch)"
    return (
        f"# Lifecycle policy: `{pol.name}`\n\n"
        f"**Source:** {src}\n\n"
        "## Policy\n\n"
        + _json_block(pol.policy)
    )


def format_elasticsearch_snapshot_repository_markdown(
    repo: ElasticsearchSnapshotRepositoryInfo,
) -> str:
    parts = [
        f"# Snapshot repository: `{repo.name}`\n\n",
        f"**Type:** `{repo.repository_type}`\n\n",
    ]
    if repo.notes:
        parts.append(f"**Context:** {repo.notes}\n\n")
    if repo.operational:
        parts.append("## Operational settings\n\n| Setting | Value |\n|---------|-------|\n")
        for k in sorted(repo.operational.keys()):
            parts.append(f"| `{k}` | `{repo.operational[k]}` |\n")
        parts.append("\n")
    if repo.settings:
        parts.append("## Provider-specific settings\n\n")
        parts.append(_json_block(repo.settings))
    elif not repo.operational:
        parts.append("_No additional settings returned by the cluster._\n\n")
    full = {**repo.operational, **repo.settings}
    if full:
        parts.append("## Full settings (JSON)\n\n")
        parts.append(_json_block(full))
    return "".join(parts)


def format_elasticsearch_search_template_markdown(tpl: ElasticsearchSearchTemplateInfo) -> str:
    parts = [
        f"# Search template: `{tpl.name}`\n\n",
        f"**Language:** `{tpl.lang}`\n\n",
    ]
    if tpl.diagnostics:
        parts.append(f"> **Diagnostics:** {tpl.diagnostics}\n\n")
    parts.append("## Summary\n\n")
    if tpl.source_length is not None:
        parts.append(f"- **Source length:** {tpl.source_length:,} characters\n")
    else:
        parts.append("- **Source length:** _unknown_\n")
    if tpl.param_keys:
        keys = ", ".join(f"`{k}`" for k in tpl.param_keys)
        parts.append(f"- **Parameter keys:** {keys}\n")
    else:
        parts.append("- **Parameter keys:** _none declared_\n")
    parts.append("\n")
    if tpl.source_preview:
        parts.append("## Query body\n\n")
        fence = "json" if tpl.source_preview.lstrip().startswith("{") else "text"
        parts.append(f"```{fence}\n{tpl.source_preview}\n```\n\n")
        if tpl.source_truncated:
            parts.append(
                "_Template source was truncated for markdown size; see full definition below._\n\n"
            )
    parts.append("## Definition\n\n")
    parts.append(_json_block(tpl.definition))
    return "".join(parts)


def format_elasticsearch_security_placeholder_markdown(
    *,
    feature: str,
    title: str,
) -> str:
    return (
        f"# {title} (reserved)\n\n"
        "> **Status:** Not implemented — intentional non-export.\n\n"
        "Security metadata export is **disabled** pending redaction and permissions design. "
        "Enabling this feature flag emits this deterministic placeholder only; "
        "**no live cluster security APIs are called** and **no secrets are written** to markdown.\n\n"
        f"**Feature flag:** `{feature}`\n\n"
        "## What is not exported\n\n"
        "- Credentials, hashed passwords, or API key secrets\n"
        "- Role privilege assignments from live `_security` APIs\n"
        "- User account details or API key metadata\n\n"
        "## Future work\n\n"
        "A future release may export redacted role names and index privilege summaries "
        "when explicit operator consent and cluster permissions are configured.\n"
    )


def format_search_architecture_markdown(ctx: ElasticsearchExportContext) -> str:
    parts = ["# Search architecture\n\n"]
    if ctx.cluster_name:
        parts.append(f"**Cluster:** `{ctx.cluster_name}`\n\n")
    parts.append(f"**Index pattern (export):** `{ctx.index_pattern}`\n\n")

    parts.append("## Overview\n\n")
    parts.append(
        "This document summarizes how search and storage objects relate in the exported "
        "Elasticsearch / OpenSearch cluster metadata bundle.\n\n"
    )

    if ctx.data_streams:
        parts.append("## Data streams and ingestion\n\n")
        parts.append("| Data stream | Index template | Backing indices |\n")
        parts.append("|-------------|----------------|-----------------|\n")
        for name, tpl, backing in ctx.data_streams:
            tpl_cell = f"`{tpl}`" if tpl else "—"
            ix_cell = ", ".join(f"`{i}`" for i in backing) if backing else "—"
            parts.append(f"| `{name}` | {tpl_cell} | {ix_cell} |\n")
        parts.append("\n")
        if ctx.pipelines:
            parts.append(
                "**Ingest pipelines:** "
                + ", ".join(f"`{p}`" for p in ctx.pipelines)
                + " — see `elasticsearch/pipelines/`.\n\n"
            )

    if ctx.index_templates or ctx.component_templates:
        parts.append("## Template inheritance\n\n")
        if ctx.component_templates:
            parts.append(
                "**Component templates:** "
                + ", ".join(f"`{c}`" for c in ctx.component_templates)
                + " — see `elasticsearch/component_templates/`.\n\n"
            )
        if ctx.index_templates:
            parts.append("| Index template | Patterns | Composed of | Legacy |\n")
            parts.append("|----------------|----------|-------------|--------|\n")
            for name, patterns, composed, legacy in ctx.index_templates:
                pat = ", ".join(f"`{p}`" for p in patterns) if patterns else "—"
                comp = ", ".join(f"`{c}`" for c in composed) if composed else "—"
                leg = "yes" if legacy else "no"
                parts.append(f"| `{name}` | {pat} | {comp} | {leg} |\n")
            parts.append("\n")

    if ctx.ilm_policies:
        parts.append("## Index lifecycle\n\n")
        for name, source in ctx.ilm_policies:
            parts.append(f"- **`{name}`** ({source}) — see `elasticsearch/ilm/{name}.md`\n")
        parts.append("\n")

    if ctx.alias_map:
        parts.append("## Alias strategy\n\n")
        parts.append(
            "Aliases route queries to concrete indices. Full mapping: "
            "[`alias_graph.md`](alias_graph.md).\n\n"
        )
        for alias in sorted(ctx.alias_map.keys())[:20]:
            targets = ctx.alias_map[alias]
            parts.append(
                f"- **`{alias}`** → {', '.join(f'`{t}`' for t in targets)}\n"
            )
        if len(ctx.alias_map) > 20:
            parts.append(f"\n_…and {len(ctx.alias_map) - 20} more aliases in `alias_graph.md`._\n")
        parts.append("\n")

    if ctx.indices:
        parts.append("## Indices sample\n\n")
        sample = ctx.indices[:30]
        parts.append(", ".join(f"`{i}`" for i in sample))
        if len(ctx.indices) > 30:
            parts.append(f" _(and {len(ctx.indices) - 30} more in `elasticsearch/indices/`)_")
        parts.append("\n\n")

    if ctx.snapshot_repositories:
        parts.append("## Snapshot repositories\n\n")
        for name, rtype in ctx.snapshot_repositories:
            parts.append(f"- **`{name}`** (`{rtype}`)\n")
        parts.append("\n")

    if ctx.search_templates:
        parts.append("## Search templates\n\n")
        parts.append(
            ", ".join(f"`{t}`" for t in ctx.search_templates)
            + " — see `elasticsearch/search_templates/`.\n\n"
        )

    parts.append("## Related documentation\n\n")
    links = [
        ("elasticsearch/indices/", "Per-index mappings and settings"),
        ("elasticsearch/data_streams/", "Data streams"),
        ("elasticsearch/component_templates/", "Component templates"),
        ("elasticsearch/templates/", "Index templates"),
        ("elasticsearch/pipelines/", "Ingest pipelines"),
        ("elasticsearch/ilm/", "Lifecycle policies"),
        ("elasticsearch/alias_graph.md", "Alias graph"),
    ]
    for rel, desc in links:
        parts.append(f"- [`{rel}`]({rel}) — {desc}\n")
    parts.append("\n")
    return "".join(parts)


def format_alias_graph_markdown(alias_to_indices: dict[str, list[str]]) -> str:
    parts = ["# Alias graph\n\n", "| Alias | Indices |\n|-------|----------|\n"]
    if not alias_to_indices:
        parts.append("| _none_ | — |\n")
        return "".join(parts)
    for alias in sorted(alias_to_indices.keys()):
        indices = alias_to_indices[alias]
        cell = ", ".join(f"`{i}`" for i in indices)
        parts.append(f"| `{alias}` | {cell} |\n")
    return "".join(parts)
