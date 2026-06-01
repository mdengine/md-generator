"""Elasticsearch adapter that reads exported JSON/ZIP bundles (no live cluster)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from md_generator.db.core.base_adapter import BaseAdapter
from md_generator.db.core.elasticsearch_bundle import load_json_map, read_json_file
from md_generator.db.core.elasticsearch_format import (
    aliases_for_index,
    extract_shard_config,
    index_pattern_from_limits,
)
from md_generator.db.core.elasticsearch_format import invert_alias_map
from md_generator.db.core.elasticsearch_normalize import (
    filter_snapshot_repositories_by_type,
    normalize_search_template,
    normalize_snapshot_repository,
)
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


class ElasticsearchJsonAdapter(BaseAdapter):
    """Read cluster metadata from an on-disk bundle (see ``elasticsearch_bundle`` layout)."""

    db_type = "elasticsearch"

    def __init__(self, bundle_dir: Path, limits: dict[str, Any]) -> None:
        self._dir = bundle_dir.resolve()
        self._limits = dict(limits or {})
        self.cluster_name: str | None = None

    def validate_connection(self) -> None:
        if not self._dir.is_dir():
            raise ValueError(f"Elasticsearch JSON bundle directory not found: {self._dir}")
        meta = self._dir / "cluster.json"
        if meta.is_file():
            data = read_json_file(meta)
            if isinstance(data, dict):
                self.cluster_name = data.get("cluster_name")

    def close(self) -> None:
        return None

    def limits(self) -> dict[str, Any]:
        return dict(self._limits)

    def list_schemas(self) -> list[str]:
        return sorted(self._index_names())

    def _index_names(self) -> list[str]:
        mappings = load_json_map(self._dir / "mappings")
        settings = load_json_map(self._dir / "settings")
        names = set(mappings.keys()) | set(settings.keys())
        bulk = self._dir / "mappings.json"
        if bulk.is_file():
            body = read_json_file(bulk)
            if isinstance(body, dict):
                names |= {k for k in body if not str(k).startswith(".")}
        return sorted(names)

    def get_alias_map(self) -> dict[str, list[str]]:
        p = self._dir / "aliases.json"
        if p.is_file():
            body = read_json_file(p)
            if isinstance(body, dict):
                return invert_alias_map(body)
        return {}

    def get_indices(self, *, include_field_caps: bool = False) -> list[ElasticsearchIndexInfo]:
        mappings_map = load_json_map(self._dir / "mappings")
        settings_map = load_json_map(self._dir / "settings")
        field_caps_map = load_json_map(self._dir / "field_caps") if include_field_caps else {}
        bulk_m = self._dir / "mappings.json"
        if bulk_m.is_file():
            body = read_json_file(bulk_m)
            if isinstance(body, dict):
                for k, v in body.items():
                    if str(k).startswith("."):
                        continue
                    if isinstance(v, dict) and "mappings" in v:
                        mappings_map.setdefault(str(k), v["mappings"])
                    else:
                        mappings_map.setdefault(str(k), v)

        alias_body: dict[str, Any] = {}
        ap = self._dir / "aliases.json"
        if ap.is_file():
            ab = read_json_file(ap)
            if isinstance(ab, dict):
                alias_body = ab

        max_ix = max(1, int(self._limits.get("max_indices", 500)))
        pattern = index_pattern_from_limits(self._limits)
        names = [n for n in self._index_names() if _match_pattern(n, pattern)][:max_ix]

        out: list[ElasticsearchIndexInfo] = []
        for name in names:
            raw_m = mappings_map.get(name, {})
            if isinstance(raw_m, dict) and "mappings" in raw_m:
                mappings = raw_m["mappings"]
            elif isinstance(raw_m, dict):
                mappings = raw_m
            else:
                mappings = {}
            raw_s = settings_map.get(name, {})
            if isinstance(raw_s, dict) and "settings" in raw_s:
                settings = raw_s["settings"]
            elif isinstance(raw_s, dict) and "index" in raw_s:
                settings = raw_s
            else:
                settings = raw_s if isinstance(raw_s, dict) else {}
            fc = field_caps_map.get(name) if include_field_caps else None
            if isinstance(fc, dict) and "fields" not in fc and "response" in fc:
                fc = fc.get("response")
            out.append(
                ElasticsearchIndexInfo(
                    name=name,
                    aliases=aliases_for_index(alias_body, name),
                    mappings=mappings if isinstance(mappings, dict) else {},
                    settings=settings if isinstance(settings, dict) else {},
                    shard_config=extract_shard_config(settings if isinstance(settings, dict) else {}),
                    field_caps=fc if isinstance(fc, dict) else None,
                )
            )
        return out

    def get_data_streams(self) -> list[ElasticsearchDataStreamInfo]:
        items = self._load_named_objects(self._dir / "data_streams")
        out: list[ElasticsearchDataStreamInfo] = []
        for name, definition in sorted(items.items()):
            if not isinstance(definition, dict):
                continue
            indices = tuple(
                str(i.get("index_name", ""))
                for i in (definition.get("indices") or [])
                if isinstance(i, dict) and i.get("index_name")
            )
            out.append(
                ElasticsearchDataStreamInfo(
                    name=name,
                    indices=indices,
                    template=definition.get("template"),
                    generation=definition.get("generation"),
                    definition=definition,
                )
            )
        return out[: self._max("max_data_streams", 500)]

    def get_component_templates(self) -> list[ElasticsearchComponentTemplateInfo]:
        items = self._load_named_objects(self._dir / "component_templates")
        out = [
            ElasticsearchComponentTemplateInfo(name=n, template=t if isinstance(t, dict) else {})
            for n, t in sorted(items.items())
            if isinstance(t, dict)
        ]
        return out[: self._max("max_component_templates", 500)]

    def get_ingest_pipelines(self) -> list[ElasticsearchPipelineInfo]:
        items = self._load_named_objects(self._dir / "pipelines")
        single = self._dir / "pipelines.json"
        if single.is_file():
            body = read_json_file(single)
            if isinstance(body, dict):
                items = {str(k): v for k, v in body.items() if isinstance(v, dict)}
        return [
            ElasticsearchPipelineInfo(name=n, definition=d)
            for n, d in sorted(items.items())[: self._max("max_pipelines", 500)]
            if isinstance(d, dict)
        ]

    def get_index_templates(self) -> list[ElasticsearchIndexTemplateInfo]:
        items = self._load_named_objects(self._dir / "templates")
        out: list[ElasticsearchIndexTemplateInfo] = []
        for name, raw in sorted(items.items()):
            if not isinstance(raw, dict):
                continue
            if "index_template" in raw:
                tpl = raw["index_template"]
                legacy = False
            else:
                tpl = raw
                legacy = bool(raw.get("index_patterns")) and "composed_of" not in raw
            patterns = tpl.get("index_patterns") or []
            if not isinstance(patterns, list):
                patterns = [patterns]
            composed = tpl.get("composed_of")
            template_body = tpl.get("template", tpl) if isinstance(tpl.get("template"), dict) else tpl
            out.append(
                ElasticsearchIndexTemplateInfo(
                    name=name,
                    index_patterns=tuple(str(p) for p in patterns),
                    priority=tpl.get("priority") or tpl.get("order"),
                    template=template_body if isinstance(template_body, dict) else {},
                    composed_of=tuple(str(c) for c in composed) if isinstance(composed, list) else None,
                    legacy=legacy,
                )
            )
        return out[: self._max("max_templates", 500)]

    def get_ilm_policies(self) -> list[ElasticsearchIlmPolicyInfo]:
        items = self._load_named_objects(self._dir / "ilm")
        source = "ilm"
        meta = self._dir / "ilm_source.txt"
        if meta.is_file() and "ism" in meta.read_text(encoding="utf-8").lower():
            source = "ism"
        return [
            ElasticsearchIlmPolicyInfo(
                name=n,
                policy=d.get("policy", d) if isinstance(d, dict) else {},
                source=source,
            )
            for n, d in sorted(items.items())[: self._max("max_ilm_policies", 200)]
            if isinstance(d, dict)
        ]

    def get_snapshot_repositories(self) -> list[ElasticsearchSnapshotRepositoryInfo]:
        items = self._load_named_objects(self._dir / "snapshots")
        single = self._dir / "snapshots.json"
        if single.is_file():
            body = read_json_file(single)
            if isinstance(body, dict):
                items = body
        items = filter_snapshot_repositories_by_type(items, self._limits)
        slm_items = self._load_named_objects(self._dir / "slm")
        slm_single = self._dir / "slm.json"
        if slm_single.is_file():
            slm_body = read_json_file(slm_single)
            if isinstance(slm_body, dict):
                slm_items = slm_body
        out: list[ElasticsearchSnapshotRepositoryInfo] = []
        for name, repo in sorted(items.items())[: self._max("max_snapshot_repositories", 100)]:
            if not isinstance(repo, dict):
                continue
            out.append(
                normalize_snapshot_repository(
                    str(name),
                    repo,
                    slm_policies=slm_items if slm_items else None,
                )
            )
        return out

    def get_search_templates(self) -> list[ElasticsearchSearchTemplateInfo]:
        items = self._load_named_objects(self._dir / "search_templates")
        out: list[ElasticsearchSearchTemplateInfo] = []
        for name, spec in sorted(items.items())[: self._max("max_search_templates", 500)]:
            if not isinstance(spec, dict):
                continue
            normalized = normalize_search_template(str(name), spec, self._limits)
            if normalized is not None:
                out.append(normalized)
        return out

    def _max(self, key: str, default: int) -> int:
        return max(1, int(self._limits.get(key, default)))

    def _load_named_objects(self, directory: Path) -> dict[str, Any]:
        return load_json_map(directory)


def _match_pattern(index_name: str, pattern: str) -> bool:
    if pattern in ("*", ""):
        return True
    if pattern.endswith("*"):
        return index_name.startswith(pattern[:-1])
    return index_name == pattern
