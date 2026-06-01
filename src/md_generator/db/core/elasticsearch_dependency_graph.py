"""Heuristic search-template dependency graph for Elasticsearch exports."""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from typing import Any

from md_generator.db.core.elasticsearch_query_classify import format_query_type_heading
from md_generator.db.core.elasticsearch_synthesis import ElasticsearchExportContext
from md_generator.db.core.models import (
    ElasticsearchIndexTemplateInfo,
    ElasticsearchSearchTemplateInfo,
)

_WILDCARD_LITERAL = re.compile(r"""['"]([^'"]*\*[^'"]*)['"]""")


@dataclass(frozen=True)
class TemplateDependencyRow:
    template_name: str
    indices: tuple[tuple[str, str], ...]
    aliases: tuple[tuple[str, str], ...]
    pipelines: tuple[tuple[str, str], ...]
    query_types: tuple[str, ...]
    confidence: str

    @property
    def has_links(self) -> bool:
        return bool(self.indices or self.aliases or self.pipelines)


def _template_source_blob(tpl: ElasticsearchSearchTemplateInfo) -> str:
    parts: list[str] = []
    if tpl.source_preview:
        parts.append(tpl.source_preview)
    parts.append(json.dumps(tpl.definition, sort_keys=True, default=str))
    return "\n".join(parts)


def _dedupe_links(items: list[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for name, confidence in items:
        if name in seen:
            continue
        seen.add(name)
        out.append((name, confidence))
    return tuple(out)


def _index_literals_from_template(tpl: ElasticsearchSearchTemplateInfo) -> list[str]:
    spec = tpl.definition
    source = spec.get("source")
    if source is None:
        script = spec.get("script")
        if isinstance(script, dict):
            source = script.get("source")
    if isinstance(source, dict):
        idx = source.get("index")
        return [str(idx)] if isinstance(idx, str) else []
    if isinstance(source, str) and source.strip().startswith("{"):
        try:
            parsed = json.loads(source)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, dict):
            idx = parsed.get("index")
            return [str(idx)] if isinstance(idx, str) else []
    return []


def _match_indices(
    source: str,
    indices: list[str],
    *,
    literals: list[str] | None = None,
) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for idx in indices:
        if idx in source:
            links.append((idx, "explicit"))
    for literal in literals or []:
        if "*" in literal:
            for idx in indices:
                if fnmatch.fnmatchcase(idx, literal):
                    links.append((idx, "inferred"))
        elif literal in indices:
            links.append((literal, "explicit"))
    for match in _WILDCARD_LITERAL.finditer(source):
        pattern = match.group(1)
        for idx in indices:
            if fnmatch.fnmatchcase(idx, pattern):
                links.append((idx, "inferred"))
    for match in re.finditer(r"([\w.\-]+\*[\w.\-]*)", source):
        pattern = match.group(1)
        if "*" not in pattern:
            continue
        for idx in indices:
            if fnmatch.fnmatchcase(idx, pattern):
                links.append((idx, "inferred"))
    return links


def _match_names(source: str, names: list[str]) -> list[tuple[str, str]]:
    return [(name, "explicit") for name in names if name in source]


def _pipelines_from_index_templates(
    templates: list[ElasticsearchIndexTemplateInfo],
) -> set[str]:
    found: set[str] = set()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ("default_pipeline", "final_pipeline") and isinstance(value, str):
                    found.add(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    for tpl in templates:
        walk(tpl.template)
    return found


def _indices_from_index_template_patterns(
    source: str,
    index_templates: list[ElasticsearchIndexTemplateInfo],
    indices: list[str],
) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for tpl in index_templates:
        for pattern in tpl.index_patterns:
            if pattern not in source and f'"{pattern}"' not in source and f"'{pattern}'" not in source:
                continue
            for idx in indices:
                if fnmatch.fnmatchcase(idx, pattern):
                    links.append((idx, "inferred"))
    return links


def _row_confidence(
    indices: tuple[tuple[str, str], ...],
    aliases: tuple[tuple[str, str], ...],
    pipelines: tuple[tuple[str, str], ...],
) -> str:
    all_links = list(indices) + list(aliases) + list(pipelines)
    if not all_links:
        return "—"
    if any(conf == "explicit" for _, conf in all_links):
        return "explicit"
    return "inferred"


def build_template_dependency_rows(
    templates: list[ElasticsearchSearchTemplateInfo],
    ctx: ElasticsearchExportContext,
    index_templates: list[ElasticsearchIndexTemplateInfo] | None = None,
) -> list[TemplateDependencyRow]:
    index_templates = index_templates or []
    indices = list(ctx.indices)
    aliases = list(ctx.alias_map.keys())
    pipelines = list(ctx.pipelines)
    template_pipelines = sorted(_pipelines_from_index_templates(index_templates))
    rows: list[TemplateDependencyRow] = []

    for tpl in templates:
        source = _template_source_blob(tpl)
        literals = _index_literals_from_template(tpl)
        idx_links = _match_indices(source, indices, literals=literals)
        idx_links.extend(_indices_from_index_template_patterns(source, index_templates, indices))
        alias_links = _match_names(source, aliases)
        pipe_links = _match_names(source, pipelines)
        for pipe in template_pipelines:
            if pipe in source:
                pipe_links.append((pipe, "inferred"))
        indices_d = _dedupe_links(idx_links)
        aliases_d = _dedupe_links(alias_links)
        pipelines_d = _dedupe_links(pipe_links)
        rows.append(
            TemplateDependencyRow(
                template_name=tpl.name,
                indices=indices_d,
                aliases=aliases_d,
                pipelines=pipelines_d,
                query_types=tpl.query_types,
                confidence=_row_confidence(indices_d, aliases_d, pipelines_d),
            )
        )
    return rows


def _cell_names(links: tuple[tuple[str, str], ...]) -> str:
    if not links:
        return "—"
    parts: list[str] = []
    for name, conf in links:
        suffix = "" if conf == "explicit" else " _(inferred)_"
        parts.append(f"`{name}`{suffix}")
    return ", ".join(parts)


def format_search_dependency_graph_markdown(
    rows: list[TemplateDependencyRow],
    *,
    index_pattern: str = "*",
) -> str:
    parts = [
        "# Search dependency graph\n\n",
        "> **Heuristic map only** — links are inferred from template source text, "
        "exported index/alias names, and index-template patterns. "
        "This is not proof of runtime query usage.\n\n",
        f"**Index pattern (export):** `{index_pattern}`\n\n",
    ]
    if not rows:
        parts.append("_No search templates exported; enable `elasticsearch_search_templates`._\n")
        return "".join(parts)

    linked = [r for r in rows if r.has_links]
    parts.append("## Template dependencies\n\n")
    parts.append(
        "| Template | Likely indices | Aliases | Pipelines | Query types | Confidence |\n"
        "|----------|----------------|---------|-----------|-------------|------------|\n"
    )
    for row in rows:
        qtypes = format_query_type_heading(row.query_types) if row.query_types else "—"
        parts.append(
            f"| `{row.template_name}` | {_cell_names(row.indices)} | {_cell_names(row.aliases)} | "
            f"{_cell_names(row.pipelines)} | {qtypes} | {row.confidence} |\n"
        )
    parts.append("\n")
    if linked:
        parts.append(
            f"_{len(linked)} of {len(rows)} templates have at least one inferred or explicit link._\n\n"
        )
    else:
        parts.append("_No explicit or inferred links detected for exported templates._\n\n")
    parts.append(
        "See also: [`search_architecture.md`](search_architecture.md), "
        "[`elasticsearch/search_templates/`](search_templates/).\n"
    )
    return "".join(parts)


def should_emit_dependency_graph(features: frozenset[str], limits: dict[str, Any]) -> bool:
    if "elasticsearch_search_dependency_graph" in features:
        return True
    emit = limits.get("emit_dependency_graph", False)
    if isinstance(emit, str):
        emit = emit.lower() not in ("false", "0", "no")
    return bool(emit) and "elasticsearch_search_architecture" in features
