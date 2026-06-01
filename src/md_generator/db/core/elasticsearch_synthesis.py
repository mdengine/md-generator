"""Collected metadata for ``search_architecture.md`` synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ElasticsearchExportContext:
    cluster_name: str | None = None
    index_pattern: str = "*"
    alias_map: dict[str, list[str]] = field(default_factory=dict)
    indices: list[str] = field(default_factory=list)
    data_streams: list[tuple[str, str | None, tuple[str, ...]]] = field(default_factory=list)
    component_templates: list[str] = field(default_factory=list)
    index_templates: list[tuple[str, tuple[str, ...], tuple[str, ...] | None, bool]] = field(
        default_factory=list
    )
    pipelines: list[str] = field(default_factory=list)
    ilm_policies: list[tuple[str, str]] = field(default_factory=list)
    snapshot_repositories: list[tuple[str, str]] = field(default_factory=list)
    search_templates: list[str] = field(default_factory=list)
