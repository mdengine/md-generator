"""Elasticsearch export branch (isolated from SQL/Mongo extractor paths)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from md_generator.db.core.base_adapter import BaseAdapter
from md_generator.db.core.elasticsearch_markdown import (
    format_alias_graph_markdown,
    format_elasticsearch_component_template_markdown,
    format_elasticsearch_data_stream_markdown,
    format_elasticsearch_ilm_markdown,
    format_elasticsearch_index_markdown,
    format_elasticsearch_index_template_markdown,
    format_elasticsearch_pipeline_markdown,
    format_elasticsearch_search_template_markdown,
    format_elasticsearch_security_placeholder_markdown,
    format_elasticsearch_snapshot_repository_markdown,
    format_search_architecture_markdown,
)
from md_generator.db.core.elasticsearch_normalize import (
    SECURITY_LIVE_EXPORT_BLOCKED,
    security_placeholder_sections,
)
from md_generator.db.core.elasticsearch_synthesis import ElasticsearchExportContext
from md_generator.db.core.export_manifest import ExportManifestBuilder
from md_generator.db.core.markdown_writer import (
    format_empty_feature_section,
    ordered_combined_readme_paths,
    slugify_segment,
    write_run_readme,
    write_text,
)
from md_generator.db.core.models import RunMetadata
from md_generator.db.core.run_config import RunConfig
from md_generator.db.core.util import redact_uri

def _guard_security_live_export(adapter: BaseAdapter) -> None:
    if not SECURITY_LIVE_EXPORT_BLOCKED:
        return
    for method in (
        "get_security_roles",
        "get_security_users",
        "get_security_api_keys",
    ):
        impl = getattr(type(adapter), method, None)
        if impl is not None and impl is not getattr(BaseAdapter, method, None):
            raise RuntimeError(
                f"Live security export via {method}() is blocked; "
                "placeholder docs only until redaction design is complete."
            )


def _emit(on_progress: Callable[[int, str], None] | None, pct: int, msg: str) -> None:
    if on_progress:
        on_progress(pct, msg)


def _flush_combined(
    root: Path,
    rel_path: str,
    parts: list[tuple[str, str]],
    *,
    on_file: Callable[[Path], None] | None,
) -> None:
    if not parts:
        return
    body = "\n\n---\n\n".join(b for _, b in sorted(parts, key=lambda x: x[0]))
    write_text(root / rel_path, body)
    if on_file:
        on_file(root / rel_path)


def _write_empty(
    root: Path,
    cfg: RunConfig,
    subdir: str,
    label: str,
    scope: str,
    *,
    on_file: Callable[[Path], None] | None,
) -> None:
    body = format_empty_feature_section(label, scope)
    if cfg.split_files:
        p = root / subdir / "README.md"
    else:
        p = root / f"{subdir.replace('/', '_')}.md"
    write_text(p, body)
    if on_file:
        on_file(p)


def _export_objects(
    *,
    cfg: RunConfig,
    root: Path,
    subdir: str,
    combined_rel: str,
    objects: list[tuple[str, str]],
    progress_prefix: str,
    on_progress: Callable[[int, str], None] | None,
    on_file: Callable[[Path], None] | None,
    notify_file: Callable[[Path], None],
    bundle_paths_written: list[str],
    empty_label: str,
    empty_scope: str,
    step_pct: int,
) -> None:
    if objects:
        combined: list[tuple[str, str]] = []
        for i, (name, body) in enumerate(objects):
            if cfg.split_files:
                p = root / subdir / f"{slugify_segment(name)}.md"
                write_text(p, body)
                notify_file(p)
            combined.append((name, body))
            _emit(
                on_progress,
                step_pct + int(8 * (i + 1) / max(len(objects), 1)),
                f"{progress_prefix}/{name}",
            )
        if combined and (
            (cfg.split_files and cfg.write_combined_feature_markdown) or not cfg.split_files
        ):
            _flush_combined(root, combined_rel, combined, on_file=on_file)
            bundle_paths_written.append(combined_rel)
    else:
        _write_empty(root, cfg, subdir, empty_label, empty_scope, on_file=on_file)


def export_elasticsearch_markdown(
    cfg: RunConfig,
    adapter: BaseAdapter,
    feats: frozenset[str],
    root: Path,
    *,
    on_progress: Callable[[int, str], None] | None = None,
    on_file: Callable[[Path], None] | None = None,
    manifest: ExportManifestBuilder | None = None,
) -> Path:
    """Write Elasticsearch metadata under ``root`` and return ``root`` (never SQL paths)."""
    _guard_security_live_export(adapter)
    bundle_paths_written: list[str] = []
    scope = str(cfg.limits.get("index_pattern") or "*")
    es_out = cfg.elasticsearch.normalized()
    cluster_name = getattr(adapter, "cluster_name", None)
    ctx = ElasticsearchExportContext(
        cluster_name=cluster_name,
        index_pattern=scope,
    )

    def notify_file(p: Path) -> None:
        if manifest is not None:
            manifest.add_file(p, root)
        if on_file:
            on_file(p)

    _EXPORT_FEATURES = (
        "elasticsearch_indices",
        "elasticsearch_data_streams",
        "elasticsearch_component_templates",
        "elasticsearch_index_templates",
        "elasticsearch_ingest_pipelines",
        "elasticsearch_ilm_policies",
        "elasticsearch_snapshot_repositories",
        "elasticsearch_search_templates",
    )
    steps = max(sum(1 for f in _EXPORT_FEATURES if f in feats), 1)
    step_i = 0
    base_pct = 10
    step_span = 70 // steps

    if "elasticsearch_indices" in feats:
        step_i += 1
        indices = adapter.get_indices(
            include_field_caps="elasticsearch_field_caps" in feats,
        )
        combined: list[tuple[str, str]] = []
        if indices:
            ctx.indices = [idx.name for idx in indices]
            for i, idx in enumerate(indices):
                body = format_elasticsearch_index_markdown(idx, output=es_out)
                if cfg.split_files:
                    p = root / "elasticsearch" / "indices" / f"{slugify_segment(idx.name)}.md"
                    write_text(p, body)
                    notify_file(p)
                combined.append((idx.name, body))
                _emit(
                    on_progress,
                    int(10 + 50 * step_i / steps * (i + 1) / max(len(indices), 1)),
                    f"elasticsearch/indices/{idx.name}",
                )
            if cfg.split_files and cfg.write_combined_feature_markdown and combined:
                _flush_combined(root, "elasticsearch/indices.md", combined, on_file=on_file)
                bundle_paths_written.append("elasticsearch/indices.md")
            elif not cfg.split_files and combined:
                _flush_combined(root, "elasticsearch/indices.md", combined, on_file=on_file)
                bundle_paths_written.append("elasticsearch/indices.md")

            if hasattr(adapter, "get_alias_map"):
                alias_map = adapter.get_alias_map()
                if alias_map:
                    ctx.alias_map = alias_map
                    p = root / "elasticsearch" / "alias_graph.md"
                    write_text(p, format_alias_graph_markdown(alias_map))
                    notify_file(p)
                    bundle_paths_written.append("elasticsearch/alias_graph.md")
        else:
            _write_empty(
                root,
                cfg,
                "elasticsearch/indices",
                "Elasticsearch indices",
                f"index pattern `{scope}`",
                on_file=on_file,
            )

    if "elasticsearch_data_streams" in feats:
        step_i += 1
        streams = adapter.get_data_streams()
        combined = []
        if streams:
            ctx.data_streams = [(ds.name, ds.template, ds.indices) for ds in streams]
            for i, ds in enumerate(streams):
                body = format_elasticsearch_data_stream_markdown(ds)
                if cfg.split_files:
                    p = root / "elasticsearch" / "data_streams" / f"{slugify_segment(ds.name)}.md"
                    write_text(p, body)
                    notify_file(p)
                combined.append((ds.name, body))
                _emit(
                    on_progress,
                    int(10 + 50 * step_i / steps * (i + 1) / max(len(streams), 1)),
                    f"elasticsearch/data_streams/{ds.name}",
                )
            if combined and (
                (cfg.split_files and cfg.write_combined_feature_markdown) or not cfg.split_files
            ):
                _flush_combined(root, "elasticsearch/data_streams.md", combined, on_file=on_file)
                bundle_paths_written.append("elasticsearch/data_streams.md")
        else:
            _write_empty(
                root,
                cfg,
                "elasticsearch/data_streams",
                "Elasticsearch data streams",
                f"pattern `{scope}`",
                on_file=on_file,
            )

    if "elasticsearch_component_templates" in feats:
        step_i += 1
        templates = adapter.get_component_templates()
        combined = []
        if templates:
            ctx.component_templates = [t.name for t in templates]
            for i, t in enumerate(templates):
                body = format_elasticsearch_component_template_markdown(t)
                if cfg.split_files:
                    p = (
                        root
                        / "elasticsearch"
                        / "component_templates"
                        / f"{slugify_segment(t.name)}.md"
                    )
                    write_text(p, body)
                    notify_file(p)
                combined.append((t.name, body))
                _emit(
                    on_progress,
                    int(10 + 50 * step_i / steps * (i + 1) / max(len(templates), 1)),
                    f"elasticsearch/component_templates/{t.name}",
                )
            if combined and (
                (cfg.split_files and cfg.write_combined_feature_markdown) or not cfg.split_files
            ):
                _flush_combined(
                    root, "elasticsearch/component_templates.md", combined, on_file=on_file
                )
                bundle_paths_written.append("elasticsearch/component_templates.md")
        else:
            _write_empty(
                root,
                cfg,
                "elasticsearch/component_templates",
                "Elasticsearch component templates",
                "cluster",
                on_file=on_file,
            )

    if "elasticsearch_index_templates" in feats:
        step_i += 1
        pct = base_pct + step_i * step_span
        templates = adapter.get_index_templates()
        ctx.index_templates = [
            (t.name, t.index_patterns, t.composed_of, t.legacy) for t in templates
        ]
        _export_objects(
            cfg=cfg,
            root=root,
            subdir="elasticsearch/templates",
            combined_rel="elasticsearch/templates.md",
            objects=[
                (t.name, format_elasticsearch_index_template_markdown(t)) for t in templates
            ],
            progress_prefix="elasticsearch/templates",
            on_progress=on_progress,
            on_file=on_file,
            notify_file=notify_file,
            bundle_paths_written=bundle_paths_written,
            empty_label="Elasticsearch index templates",
            empty_scope="cluster",
            step_pct=pct,
        )

    if "elasticsearch_ingest_pipelines" in feats:
        step_i += 1
        pct = base_pct + step_i * step_span
        pipelines = adapter.get_ingest_pipelines()
        ctx.pipelines = [p.name for p in pipelines]
        _export_objects(
            cfg=cfg,
            root=root,
            subdir="elasticsearch/pipelines",
            combined_rel="elasticsearch/pipelines.md",
            objects=[
                (p.name, format_elasticsearch_pipeline_markdown(p)) for p in pipelines
            ],
            progress_prefix="elasticsearch/pipelines",
            on_progress=on_progress,
            on_file=on_file,
            notify_file=notify_file,
            bundle_paths_written=bundle_paths_written,
            empty_label="Elasticsearch ingest pipelines",
            empty_scope="cluster",
            step_pct=pct,
        )

    if "elasticsearch_ilm_policies" in feats:
        step_i += 1
        pct = base_pct + step_i * step_span
        policies = adapter.get_ilm_policies()
        ctx.ilm_policies = [(p.name, p.source) for p in policies]
        _export_objects(
            cfg=cfg,
            root=root,
            subdir="elasticsearch/ilm",
            combined_rel="elasticsearch/ilm.md",
            objects=[(p.name, format_elasticsearch_ilm_markdown(p)) for p in policies],
            progress_prefix="elasticsearch/ilm",
            on_progress=on_progress,
            on_file=on_file,
            notify_file=notify_file,
            bundle_paths_written=bundle_paths_written,
            empty_label="Elasticsearch ILM policies",
            empty_scope="cluster (ILM or OpenSearch ISM)",
            step_pct=pct,
        )

    if "elasticsearch_snapshot_repositories" in feats:
        step_i += 1
        pct = base_pct + step_i * step_span
        repos = adapter.get_snapshot_repositories()
        ctx.snapshot_repositories = [(r.name, r.repository_type) for r in repos]
        _export_objects(
            cfg=cfg,
            root=root,
            subdir="elasticsearch/snapshots",
            combined_rel="elasticsearch/snapshots.md",
            objects=[
                (r.name, format_elasticsearch_snapshot_repository_markdown(r)) for r in repos
            ],
            progress_prefix="elasticsearch/snapshots",
            on_progress=on_progress,
            on_file=on_file,
            notify_file=notify_file,
            bundle_paths_written=bundle_paths_written,
            empty_label="Elasticsearch snapshot repositories",
            empty_scope="cluster",
            step_pct=pct,
        )

    if "elasticsearch_search_templates" in feats:
        step_i += 1
        pct = base_pct + step_i * step_span
        templates = adapter.get_search_templates()
        ctx.search_templates = [t.name for t in templates]
        diag = None
        if hasattr(adapter, "get_search_template_export_diagnostics"):
            diag = adapter.get_search_template_export_diagnostics()
        _export_objects(
            cfg=cfg,
            root=root,
            subdir="elasticsearch/search_templates",
            combined_rel="elasticsearch/search_templates.md",
            objects=[
                (t.name, format_elasticsearch_search_template_markdown(t)) for t in templates
            ],
            progress_prefix="elasticsearch/search_templates",
            on_progress=on_progress,
            on_file=on_file,
            notify_file=notify_file,
            bundle_paths_written=bundle_paths_written,
            empty_label="Elasticsearch search templates",
            empty_scope="cluster (stored scripts; see limits.search_templates_langs)",
            step_pct=pct,
        )
        if diag:
            diag_path = root / "elasticsearch" / "search_templates" / "_diagnostics.md"
            write_text(
                diag_path,
                "# Search template export diagnostics\n\n"
                f"> {diag}\n\n"
                "Stored script APIs may be restricted on this cluster. "
                "No template bodies were exported from the failed request path.\n",
            )
            notify_file(diag_path)
            bundle_paths_written.append("elasticsearch/search_templates/_diagnostics.md")

    for feature, subdir, title in security_placeholder_sections():
        if feature not in feats:
            continue
        rel = f"elasticsearch/security/{subdir}.md"
        p = root / rel
        write_text(
            p,
            format_elasticsearch_security_placeholder_markdown(feature=feature, title=title),
        )
        notify_file(p)
        bundle_paths_written.append(rel)

    if "elasticsearch_search_architecture" in feats:
        if not ctx.alias_map and hasattr(adapter, "get_alias_map"):
            ctx.alias_map = adapter.get_alias_map()
        alias_path = root / "elasticsearch" / "alias_graph.md"
        if ctx.alias_map and not alias_path.is_file():
            write_text(alias_path, format_alias_graph_markdown(ctx.alias_map))
            notify_file(alias_path)
            bundle_paths_written.append("elasticsearch/alias_graph.md")
        p = root / "elasticsearch" / "search_architecture.md"
        write_text(p, format_search_architecture_markdown(ctx))
        notify_file(p)
        bundle_paths_written.append("elasticsearch/search_architecture.md")

    if "elasticsearch_field_caps" in feats and "elasticsearch_indices" not in feats:
        p = root / "elasticsearch" / "field_caps.md"
        write_text(
            p,
            "# Field capabilities\n\n"
            "_Enable `elasticsearch_indices` to collect field_caps per index._\n",
        )
        notify_file(p)

    erd_note: str | None = None
    if "erd" in feats:
        erd_note = "ER diagrams are not generated for Elasticsearch exports (no relational FK metadata)."

    merge_paths = (
        ordered_combined_readme_paths(bundle_paths_written)
        if cfg.readme_feature_merge != "none"
        else ()
    )
    meta = RunMetadata(
        db_type=adapter.db_type,
        uri_display=redact_uri(cfg.uri),
        schema=cfg.schema,
        database=cfg.database,
        included_features=tuple(sorted(feats)),
        limits=dict(cfg.limits),
        erd_artifacts=(),
        erd_note=erd_note,
        erd_engine=None,
        readme_feature_merge=cfg.readme_feature_merge,
        combined_readme_paths=merge_paths,
        cluster_name=cluster_name,
    )
    readme = write_run_readme(root, meta)
    notify_file(readme)
    _emit(on_progress, 100, "README.md")
    return root
