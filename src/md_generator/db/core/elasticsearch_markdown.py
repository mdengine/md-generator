"""Markdown formatters for Elasticsearch exports."""

from __future__ import annotations

from typing import Any

from md_generator.db.core.elasticsearch_format import (
    analyzer_chain_lines,
    extract_analysis,
    field_caps_table_rows,
    flatten_mapping_properties,
    settings_without_analysis,
    summarize_mapping_properties,
)
from md_generator.db.core.elasticsearch_json import json_block
from md_generator.db.core.elasticsearch_operational_notes import (
    format_mapping_summary_markdown,
    format_operational_notes_markdown,
    mapping_complexity_metrics,
    operational_notes_for_data_stream,
    operational_notes_for_ilm,
    operational_notes_for_index,
    operational_notes_for_search_template,
    operational_notes_for_slm,
    operational_notes_for_snapshot,
)
from md_generator.db.core.elasticsearch_query_classify import (
    HYBRID_SEARCH,
    SEMANTIC_SEARCH,
    VECTOR_SEARCH,
    QUERY_TYPE_LABELS,
    format_query_type_heading,
)
from md_generator.db.core.elasticsearch_output import ElasticsearchOutputConfig
from md_generator.db.core.elasticsearch_synthesis import (
    CompatibilityProbes,
    should_show_opensearch_matrix,
    compatibility_matrix_rows,
)
from md_generator.db.core.elasticsearch_synthesis import ElasticsearchExportContext
from md_generator.db.core.elasticsearch_warnings import finalize_markdown_with_warnings
from md_generator.db.core.models import (
    ElasticsearchComponentTemplateInfo,
    ElasticsearchDataStreamInfo,
    ElasticsearchIndexInfo,
    ElasticsearchIndexTemplateInfo,
    ElasticsearchIlmPolicyInfo,
    ElasticsearchPipelineInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSlmPolicyInfo,
    ElasticsearchSnapshotRepositoryInfo,
)


def _default_output() -> ElasticsearchOutputConfig:
    return ElasticsearchOutputConfig().normalized()


def _jb(
    obj: Any,
    output: ElasticsearchOutputConfig,
    warnings: list[str] | None,
    *,
    label: str = "JSON",
) -> str:
    return json_block(
        obj,
        max_chars=output.max_json_block_chars,
        warnings=warnings,
        label=label,
    )


def format_elasticsearch_index_markdown(
    idx: ElasticsearchIndexInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
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

    mappings_root = idx.mappings if isinstance(idx.mappings, dict) else None
    props = mappings_root.get("properties") if mappings_root else None
    if props is None and mappings_root:
        props = mappings_root

    mapping_metrics: dict[str, Any] | None = None
    if mappings_root is not None:
        mapping_metrics = mapping_complexity_metrics(
            props if isinstance(props, dict) else None,
            mappings_root=mappings_root,
        )

    mode = out.mapping_mode
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
            parts.append(_jb(summary["types"], out, warnings, label="Mapping types summary"))
        elif mode == "raw":
            parts.append("## Mappings\n\n")
            parts.append(_jb(idx.mappings, out, warnings, label="Mappings"))

        if out.include_raw_json and mode != "raw":
            parts.append("## Mappings (raw JSON)\n\n")
            parts.append(_jb(idx.mappings, out, warnings, label="Mappings (raw JSON)"))
    elif idx.mappings:
        parts.append("## Mappings\n\n")
        parts.append(_jb(idx.mappings, out, warnings, label="Mappings"))

    if mapping_metrics is not None:
        summary_md = format_mapping_summary_markdown(mapping_metrics)
        if summary_md:
            parts.append(summary_md)

    analysis = extract_analysis(idx.settings)
    if analysis:
        af = out.analyzer_format
        if af in ("chain", "both"):
            chains = analyzer_chain_lines(analysis)
            if chains:
                parts.append("## Analyzer chains\n\n")
                for aname, chain in chains:
                    parts.append(f"- **`{aname}`:** `{chain}`\n")
                parts.append("\n")
        if af in ("json", "both"):
            parts.append("## Analyzers (JSON)\n\n")
            parts.append(_jb(analysis, out, warnings, label="Analyzers"))

    remaining = settings_without_analysis(idx.settings)
    if remaining:
        parts.append("## Settings\n\n")
        parts.append(_jb(remaining, out, warnings, label="Settings"))

    if idx.field_caps:
        rows = field_caps_table_rows(idx.field_caps)
        parts.append("## Field capabilities\n\n")
        if rows:
            parts.append("| Field | Type | Capabilities |\n|-------|------|-------------|\n")
            for field, ftype, caps in rows:
                parts.append(f"| `{field}` | `{ftype}` | {caps or '—'} |\n")
            parts.append("\n")
        elif not out.include_raw_json:
            parts.append("_No field capability rows returned._\n\n")
            if warnings is not None:
                warnings.append("Field caps incomplete or empty for this index")
        if out.include_raw_json:
            parts.append("### Field capabilities (raw JSON)\n\n")
            parts.append(_jb(idx.field_caps, out, warnings, label="Field capabilities"))

    index_notes_md = format_operational_notes_markdown(
        operational_notes_for_index(idx, mapping_metrics)
    )
    if index_notes_md:
        parts.append(index_notes_md)

    return finalize_markdown_with_warnings("".join(parts), warnings or [])


def format_elasticsearch_data_stream_markdown(
    ds: ElasticsearchDataStreamInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
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
    ds_notes_md = format_operational_notes_markdown(operational_notes_for_data_stream(ds))
    if ds_notes_md:
        parts.append(ds_notes_md)
    parts.append("## Definition\n\n")
    parts.append(_jb(ds.definition, out, warnings, label="Data stream definition"))
    return finalize_markdown_with_warnings("".join(parts), warnings or [])


def format_elasticsearch_component_template_markdown(
    t: ElasticsearchComponentTemplateInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
    body = (
        f"# Component template: `{t.name}`\n\n"
        "## Template\n\n"
        + _jb(t.template, out, warnings, label="Component template")
    )
    return finalize_markdown_with_warnings(body, warnings or [])


def format_elasticsearch_pipeline_markdown(
    p: ElasticsearchPipelineInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
    body = (
        f"# Ingest pipeline: `{p.name}`\n\n## Definition\n\n"
        + _jb(p.definition, out, warnings, label="Pipeline definition")
    )
    return finalize_markdown_with_warnings(body, warnings or [])


def format_elasticsearch_index_template_markdown(
    t: ElasticsearchIndexTemplateInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
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
    parts.append(_jb(t.template, out, warnings, label="Index template body"))
    return finalize_markdown_with_warnings("".join(parts), warnings or [])


def format_elasticsearch_ilm_markdown(
    pol: ElasticsearchIlmPolicyInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
    src = "ISM (OpenSearch)" if pol.source == "ism" else "ILM (Elasticsearch)"
    parts = [
        f"# Lifecycle policy: `{pol.name}`\n\n",
        f"**Source:** {src}\n\n",
    ]
    ilm_notes_md = format_operational_notes_markdown(operational_notes_for_ilm(pol))
    if ilm_notes_md:
        parts.append(ilm_notes_md)
    parts.append("## Policy\n\n")
    parts.append(_jb(pol.policy, out, warnings, label="ILM policy"))
    return finalize_markdown_with_warnings("".join(parts), warnings or [])


def format_elasticsearch_slm_markdown(
    pol: ElasticsearchSlmPolicyInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
    parts = [f"# SLM policy: `{pol.name}`\n\n"]
    if pol.schedule:
        parts.append(f"**Schedule:** `{pol.schedule}`\n\n")
    if pol.repository:
        parts.append(f"**Repository:** `{pol.repository}`\n\n")
    if pol.indices_pattern:
        parts.append(f"**Indices:** `{pol.indices_pattern}`\n\n")
    slm_notes_md = format_operational_notes_markdown(operational_notes_for_slm(pol))
    if slm_notes_md:
        parts.append(slm_notes_md)
    parts.append("## Policy\n\n")
    parts.append(_jb(pol.policy, out, warnings, label="SLM policy"))
    return finalize_markdown_with_warnings("".join(parts), warnings or [])


def format_elasticsearch_snapshot_repository_markdown(
    repo: ElasticsearchSnapshotRepositoryInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
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
    snap_notes_md = format_operational_notes_markdown(operational_notes_for_snapshot(repo))
    if snap_notes_md:
        parts.append(snap_notes_md)
    if repo.settings:
        parts.append("## Provider-specific settings\n\n")
        parts.append(_jb(repo.settings, out, warnings, label="Snapshot settings"))
    elif not repo.operational:
        parts.append("_No additional settings returned by the cluster._\n\n")
    full = {**repo.operational, **repo.settings}
    if full:
        parts.append("## Full settings (JSON)\n\n")
        parts.append(_jb(full, out, warnings, label="Snapshot full settings"))
    return finalize_markdown_with_warnings("".join(parts), warnings or [])


def format_elasticsearch_search_template_markdown(
    tpl: ElasticsearchSearchTemplateInfo,
    *,
    output: ElasticsearchOutputConfig | None = None,
    warnings: list[str] | None = None,
) -> str:
    out = output.normalized() if output else _default_output()
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
    if tpl.query_types:
        parts.append(
            f"- **Query types:** {format_query_type_heading(tpl.query_types)}\n"
        )
    parts.append("\n")
    parts.append("## Query type\n\n")
    parts.append(format_query_type_heading(tpl.query_types) + "\n\n")
    tpl_notes_md = format_operational_notes_markdown(
        operational_notes_for_search_template(tpl)
    )
    if tpl_notes_md:
        parts.append(tpl_notes_md)
    if tpl.source_preview:
        parts.append("## Query body\n\n")
        fence = "json" if tpl.source_preview.lstrip().startswith("{") else "text"
        parts.append(f"```{fence}\n{tpl.source_preview}\n```\n\n")
        if tpl.source_truncated:
            parts.append(
                "_Template source was truncated for markdown size; see full definition below._\n\n"
            )
            if warnings is not None:
                warnings.append("Template source preview truncated (see limits.max_template_source_chars)")
    parts.append("## Definition\n\n")
    parts.append(_jb(tpl.definition, out, warnings, label="Search template definition"))
    return finalize_markdown_with_warnings("".join(parts), warnings or [])


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
        "This document narrates the exported cluster metadata lifecycle: ingestion, indexing, "
        "retention, search, backup, and vector/AI readiness. Object lists link to per-entity "
        "markdown under `elasticsearch/`.\n\n"
    )

    _append_ingestion_section(parts, ctx)
    _append_indexing_section(parts, ctx)
    _append_retention_section(parts, ctx)
    _append_search_section(parts, ctx)
    _append_backup_section(parts, ctx)
    _append_alias_routing_section(parts, ctx)
    _append_vector_readiness_section(parts, ctx)
    if ctx.compatibility and should_show_opensearch_matrix(ctx.compatibility):
        parts.append(format_opensearch_compatibility_markdown(ctx.compatibility))

    parts.append("## Related documentation\n\n")
    links = [
        ("elasticsearch/indices/", "Per-index mappings and settings"),
        ("elasticsearch/data_streams/", "Data streams"),
        ("elasticsearch/component_templates/", "Component templates"),
        ("elasticsearch/templates/", "Index templates"),
        ("elasticsearch/pipelines/", "Ingest pipelines"),
        ("elasticsearch/ilm/", "Lifecycle policies"),
        ("elasticsearch/slm/", "SLM snapshot policies"),
        ("elasticsearch/snapshots/", "Snapshot repositories"),
        ("elasticsearch/search_templates/", "Search templates"),
        ("elasticsearch/alias_graph.md", "Alias graph"),
        ("elasticsearch/search_dependency_graph.md", "Search template dependency graph"),
    ]
    for rel, desc in links:
        parts.append(f"- [`{rel}`]({rel}) — {desc}\n")
    parts.append("\n")
    return "".join(parts)


def format_opensearch_compatibility_markdown(probes: CompatibilityProbes) -> str:
    parts = ["## OpenSearch Compatibility\n\n"]
    if probes.opensearch_mode:
        parts.append(
            "_OpenSearch mode is enabled (`limits.opensearch: true`). "
            "Export probes reflect ISM and API compatibility for this cluster._\n\n"
        )
    else:
        parts.append(
            "_Capability matrix derived from export-time API probes and configured features._\n\n"
        )
    parts.append("| Feature | Elasticsearch | This export |\n")
    parts.append("|---------|---------------|-------------|\n")
    for feature, es_native, export_status in compatibility_matrix_rows(probes):
        parts.append(f"| {feature} | {es_native} | {export_status} |\n")
    if probes.slm_diagnostics:
        parts.append(f"\n_SLM probe note: {probes.slm_diagnostics}_\n")
    if probes.search_templates_diagnostics:
        parts.append(
            f"\n_Search template probe note: {probes.search_templates_diagnostics}_\n"
        )
    parts.append("\n")
    return "".join(parts)


def _append_ingestion_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    has_ingestion = bool(ctx.data_streams or ctx.pipelines or ctx.index_templates)
    if not has_ingestion:
        return
    parts.append("## Ingestion\n\n")
    if ctx.data_streams:
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
    if ctx.index_templates:
        parts.append("| Index template | Patterns | Composed of | Legacy |\n")
        parts.append("|----------------|----------|-------------|--------|\n")
        for name, patterns, composed, legacy in ctx.index_templates:
            pat = ", ".join(f"`{p}`" for p in patterns) if patterns else "—"
            comp = ", ".join(f"`{c}`" for c in composed) if composed else "—"
            leg = "yes" if legacy else "no"
            parts.append(f"| `{name}` | {pat} | {comp} | {leg} |\n")
        parts.append("\n")


def _append_indexing_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    has_indexing = bool(
        ctx.component_templates or ctx.index_templates or ctx.mapping_aggregate or ctx.indices
    )
    if not has_indexing:
        return
    parts.append("## Indexing\n\n")
    if ctx.component_templates:
        parts.append(
            "**Component templates:** "
            + ", ".join(f"`{c}`" for c in ctx.component_templates)
            + " — see `elasticsearch/component_templates/`.\n\n"
        )
    agg = ctx.mapping_aggregate
    if agg and agg.index_count:
        parts.append("### Mapping summary (aggregate)\n\n")
        parts.append(f"- **Indices exported:** {agg.index_count:,}\n")
        parts.append(f"- **Total mapped fields:** {agg.total_fields:,}\n")
        if agg.nested_fields:
            parts.append(f"- **Nested fields:** {agg.nested_fields:,}\n")
        if agg.dense_vector_fields:
            parts.append(f"- **Dense vector fields:** {agg.dense_vector_fields:,}\n")
        if agg.sparse_vector_fields:
            parts.append(f"- **Sparse vector fields:** {agg.sparse_vector_fields:,}\n")
        if agg.semantic_text_fields:
            parts.append(f"- **Semantic text fields:** {agg.semantic_text_fields:,}\n")
        parts.append("\n")
    elif ctx.indices:
        parts.append(f"**Indices:** {len(ctx.indices):,} exported — see `elasticsearch/indices/`.\n\n")


def _append_retention_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    if not ctx.ilm_policies and not ctx.slm_policies:
        return
    parts.append("## Retention\n\n")
    if ctx.ilm_policies:
        parts.append("### Index lifecycle (ILM / ISM)\n\n")
        for name, source in ctx.ilm_policies:
            label = "ISM" if source == "ism" else "ILM"
            parts.append(f"- **`{name}`** ({label}) — see `elasticsearch/ilm/{name}.md`\n")
        parts.append("\n")
    if ctx.slm_policies:
        parts.append("### Snapshot lifecycle (SLM)\n\n")
        for name, repo in ctx.slm_policies:
            repo_cell = f"`{repo}`" if repo else "—"
            parts.append(
                f"- **`{name}`** → repository {repo_cell} — see `elasticsearch/slm/{name}.md`\n"
            )
        parts.append("\n")


def _append_search_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    if not ctx.search_templates and not ctx.alias_map:
        return
    parts.append("## Search\n\n")
    if ctx.search_templates:
        parts.append(
            "**Search templates:** "
            + ", ".join(f"`{t}`" for t in ctx.search_templates[:30])
        )
        if len(ctx.search_templates) > 30:
            parts.append(f" _(and {len(ctx.search_templates) - 30} more)_")
        parts.append(" — see `elasticsearch/search_templates/`.\n\n")
    summary = ctx.query_type_summary
    if summary and summary.counts:
        parts.append("### Query type summary\n\n")
        parts.append("| Query type | Templates |\n|------------|----------|\n")
        for qt in sorted(summary.counts.keys()):
            label = QUERY_TYPE_LABELS.get(qt, qt.replace("_", " ").title())
            parts.append(f"| {label} | {summary.counts[qt]:,} |\n")
        parts.append("\n")
    if ctx.search_template_types:
        typed = [(n, ts) for n, ts in ctx.search_template_types if ts]
        if typed:
            parts.append("| Template | Query types |\n|----------|-------------|\n")
            for name, types in typed[:20]:
                parts.append(f"| `{name}` | {format_query_type_heading(types)} |\n")
            if len(typed) > 20:
                parts.append(
                    f"\n_…and {len(typed) - 20} more templates in `elasticsearch/search_templates/`._\n"
                )
            parts.append("\n")


def _append_backup_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    if not ctx.snapshot_repositories and not ctx.slm_policies:
        return
    parts.append("## Backup\n\n")
    if ctx.snapshot_repositories:
        parts.append("**Snapshot repositories:**\n\n")
        for name, rtype in ctx.snapshot_repositories:
            parts.append(f"- **`{name}`** (`{rtype}`)\n")
        parts.append("\nSee `elasticsearch/snapshots/` for repository details.\n\n")
    if ctx.slm_policies:
        parts.append(
            f"**SLM policies:** {len(ctx.slm_policies)} configured — "
            "automated snapshots target the repositories above.\n\n"
        )


def _append_alias_routing_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    if not ctx.alias_map:
        return
    parts.append("## Alias routing\n\n")
    parts.append(
        "Aliases route queries to concrete indices. Full mapping: "
        "[`alias_graph.md`](alias_graph.md).\n\n"
    )
    for alias in sorted(ctx.alias_map.keys())[:20]:
        targets = ctx.alias_map[alias]
        parts.append(f"- **`{alias}`** → {', '.join(f'`{t}`' for t in targets)}\n")
    if len(ctx.alias_map) > 20:
        parts.append(f"\n_…and {len(ctx.alias_map) - 20} more aliases in `alias_graph.md`._\n")
    parts.append("\n")


def _append_vector_readiness_section(parts: list[str], ctx: ElasticsearchExportContext) -> None:
    agg = ctx.mapping_aggregate
    summary = ctx.query_type_summary
    vector_indices = agg.indices_with_vectors if agg else []
    hybrid_count = summary.counts.get(HYBRID_SEARCH, 0) if summary else 0
    vector_tpl_count = summary.counts.get(VECTOR_SEARCH, 0) if summary else 0
    semantic_tpl_count = summary.counts.get(SEMANTIC_SEARCH, 0) if summary else 0
    has_vector = bool(
        vector_indices
        or hybrid_count
        or vector_tpl_count
        or semantic_tpl_count
        or (agg and (agg.dense_vector_fields or agg.sparse_vector_fields or agg.semantic_text_fields))
    )
    if not has_vector:
        return
    parts.append("## Vector / AI readiness\n\n")
    if agg:
        if agg.dense_vector_fields:
            parts.append(
                f"- **Dense vector fields:** {agg.dense_vector_fields:,} across "
                f"{len(vector_indices):,} index(es)\n"
            )
        if agg.sparse_vector_fields:
            parts.append(f"- **Sparse vector fields:** {agg.sparse_vector_fields:,}\n")
        if agg.semantic_text_fields:
            parts.append(f"- **Semantic text fields:** {agg.semantic_text_fields:,}\n")
    if vector_indices:
        sample = vector_indices[:15]
        parts.append(
            "- **Indices with vector mappings:** "
            + ", ".join(f"`{n}`" for n in sample)
        )
        if len(vector_indices) > 15:
            parts.append(f" _(and {len(vector_indices) - 15} more)_")
        parts.append("\n")
    if hybrid_count:
        parts.append(f"- **Hybrid search templates:** {hybrid_count:,}\n")
    if vector_tpl_count:
        parts.append(f"- **Vector search templates:** {vector_tpl_count:,}\n")
    if semantic_tpl_count:
        parts.append(f"- **Semantic search templates:** {semantic_tpl_count:,}\n")
    if hybrid_count and vector_indices:
        parts.append(
            "- **Hybrid search likely:** cluster has vector field mappings and hybrid query templates.\n"
        )
    parts.append("\n")


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
