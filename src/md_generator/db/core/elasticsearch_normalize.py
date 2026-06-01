"""Normalization helpers for snapshot repositories and search templates."""

from __future__ import annotations

from typing import Any

from md_generator.db.core.models import (
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSnapshotRepositoryInfo,
)

_SNAPSHOT_OPERATIONAL_KEYS = (
    "location",
    "bucket",
    "base_path",
    "readonly",
    "compress",
    "chunk_size",
    "max_restore_bytes_per_sec",
    "max_snapshot_bytes_per_sec",
    "delegate_type",
    "protocol",
    "region",
    "endpoint",
    "path_style_access",
    "storage_class",
)

_SECURITY_PLACEHOLDER_FEATURES: tuple[tuple[str, str, str], ...] = (
    ("elasticsearch_security_roles", "roles", "Elasticsearch security roles"),
    ("elasticsearch_security_users", "users", "Elasticsearch security users"),
    ("elasticsearch_security_api_keys", "api_keys", "Elasticsearch security API keys"),
)

# Guardrail: live `_security` API export must remain disabled until explicitly designed.
SECURITY_LIVE_EXPORT_BLOCKED = True


def security_placeholder_sections() -> tuple[tuple[str, str, str], ...]:
    return _SECURITY_PLACEHOLDER_FEATURES


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def _repo_settings_block(repo: dict[str, Any]) -> dict[str, Any]:
    settings = repo.get("settings")
    if isinstance(settings, dict):
        merged = dict(settings)
        for k, v in repo.items():
            if k not in ("type", "settings"):
                merged.setdefault(k, v)
        return merged
    return {k: v for k, v in repo.items() if k != "type"}


def normalize_snapshot_repository(
    name: str,
    repo: dict[str, Any],
    *,
    slm_policies: dict[str, Any] | None = None,
) -> ElasticsearchSnapshotRepositoryInfo:
    repo_type = str(repo.get("type", "unknown"))
    settings_block = _repo_settings_block(repo)
    operational: dict[str, Any] = {}
    remaining: dict[str, Any] = {}
    for k, v in sorted(settings_block.items()):
        if k in _SNAPSHOT_OPERATIONAL_KEYS:
            operational[k] = v
        else:
            remaining[k] = v

    notes: list[str] = []
    if slm_policies:
        linked: list[str] = []
        for pol_name, pol in slm_policies.items():
            if not isinstance(pol, dict):
                continue
            body = pol.get("policy", pol)
            if isinstance(body, dict) and body.get("repository") == name:
                linked.append(str(pol_name))
        if linked:
            notes.append("SLM policies: " + ", ".join(sorted(set(linked))))

    return ElasticsearchSnapshotRepositoryInfo(
        name=name,
        repository_type=repo_type,
        settings=remaining,
        operational=operational,
        notes="; ".join(notes) if notes else None,
    )


def _extract_script_source(spec: dict[str, Any]) -> Any:
    if "source" in spec:
        return spec["source"]
    script = spec.get("script")
    if isinstance(script, dict):
        return script.get("source", script)
    return None


def _extract_param_keys(spec: dict[str, Any]) -> tuple[str, ...]:
    params = spec.get("params")
    if not isinstance(params, dict):
        script = spec.get("script")
        if isinstance(script, dict):
            params = script.get("params")
    if isinstance(params, dict):
        return tuple(sorted(str(k) for k in params.keys()))
    return ()


def _allowed_search_template_langs(limits: dict[str, Any]) -> frozenset[str]:
    raw = limits.get("search_templates_langs", "mustache")
    langs = _as_str_list(raw)
    if not langs:
        return frozenset({"mustache"})
    return frozenset(x.lower() for x in langs)


def normalize_search_template(
    name: str,
    spec: dict[str, Any],
    limits: dict[str, Any],
) -> ElasticsearchSearchTemplateInfo | None:
    if not isinstance(spec, dict):
        return None
    lang = str(spec.get("lang", "")).lower()
    allowed = _allowed_search_template_langs(limits)
    if lang and lang not in allowed:
        return None
    if not lang and "mustache" not in allowed:
        return None

    source = _extract_script_source(spec)
    max_chars = int(limits.get("max_template_source_chars", 8000))
    source_preview: str | None = None
    truncated = False
    if source is not None:
        if isinstance(source, dict):
            import json

            text = json.dumps(source, sort_keys=True)
        else:
            text = str(source)
        if len(text) > max_chars:
            source_preview = text[:max_chars] + "\n… (truncated)"
            truncated = True
        else:
            source_preview = text

    return ElasticsearchSearchTemplateInfo(
        name=name,
        lang=lang or "mustache",
        definition=spec,
        param_keys=_extract_param_keys(spec),
        source_length=len(str(source)) if source is not None else None,
        source_preview=source_preview,
        source_truncated=truncated,
        diagnostics=None,
    )


def filter_snapshot_repositories_by_type(
    repos: dict[str, Any],
    limits: dict[str, Any],
) -> dict[str, Any]:
    allowed = _as_str_list(limits.get("snapshot_repository_types"))
    if not allowed:
        return repos
    allowed_set = {t.lower() for t in allowed}
    out: dict[str, Any] = {}
    for name, repo in repos.items():
        if not isinstance(repo, dict):
            continue
        if str(repo.get("type", "")).lower() in allowed_set:
            out[name] = repo
    return out
