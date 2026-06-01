"""Elasticsearch / OpenSearch introspection adapter."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from md_generator.db.core.base_adapter import BaseAdapter
from md_generator.db.core.elasticsearch_format import (
    aliases_for_index,
    extract_shard_config,
    field_caps_table_rows,
    index_pattern_from_limits,
    parse_cat_index_row,
)
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

logger = logging.getLogger(__name__)


def _as_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() not in ("false", "0", "no")


class ElasticsearchAdapter(BaseAdapter):
    db_type = "elasticsearch"

    def __init__(self, uri: str, limits: dict[str, Any]) -> None:
        self._uri = (uri or "").strip()
        self._limits = dict(limits or {})
        self._client: Any = None
        self.cluster_name: str | None = None
        self._search_template_diagnostics: str | None = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from elasticsearch import Elasticsearch
        except ImportError as e:
            raise ImportError(
                'Elasticsearch export requires the db extra: pip install "mdengine[db]"'
            ) from e
        parsed = urlparse(self._uri)
        kwargs: dict[str, Any] = {}
        if parsed.username is not None and parsed.password is not None:
            kwargs["basic_auth"] = (parsed.username, parsed.password)
        kwargs["verify_certs"] = _as_bool(self._limits.get("verify_certs"), True)
        self._client = Elasticsearch(hosts=[self._uri], **kwargs)
        return self._client

    def validate_connection(self) -> None:
        if not self._uri:
            raise ValueError("database.uri is required for Elasticsearch")
        client = self._ensure_client()
        if not client.ping():
            raise ConnectionError("Elasticsearch cluster did not respond to ping")
        try:
            info = client.info()
            self.cluster_name = info.get("cluster_name") if isinstance(info, dict) else None
        except Exception:
            self.cluster_name = None

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def limits(self) -> dict[str, Any]:
        return dict(self._limits)

    def _expand_wildcards(self) -> str:
        if _as_bool(self._limits.get("include_closed_indices"), False):
            return "open,closed,hidden"
        return "open"

    def _index_pattern(self) -> str:
        return index_pattern_from_limits(self._limits)

    def _max(self, key: str, default: int) -> int:
        return max(1, int(self._limits.get(key, default)))

    def list_schemas(self) -> list[str]:
        """Index names (ES vocabulary); used by ``--list-schemas`` / ``--list-indices``."""
        client = self._ensure_client()
        pattern = self._index_pattern()
        try:
            rows = client.cat.indices(index=pattern, format="json", expand_wildcards=self._expand_wildcards())
            if isinstance(rows, list):
                names = [str(r.get("index", "")) for r in rows if r.get("index")]
                return sorted(set(names))
        except Exception as e:
            logger.warning("cat.indices failed: %s", e)
        return []

    def get_alias_map(self) -> dict[str, list[str]]:
        """alias name -> backing index names."""
        from md_generator.db.core.elasticsearch_format import invert_alias_map

        client = self._ensure_client()
        pattern = self._index_pattern()
        try:
            body = client.indices.get_alias(index=pattern, expand_wildcards=self._expand_wildcards())
            if isinstance(body, dict):
                return invert_alias_map(body)
        except Exception as e:
            logger.warning("get_alias failed: %s", e)
        return {}

    def get_indices(self, *, include_field_caps: bool = False) -> list[ElasticsearchIndexInfo]:
        client = self._ensure_client()
        pattern = self._index_pattern()
        expand = self._expand_wildcards()
        max_ix = self._max("max_indices", 500)

        cat_by_name: dict[str, dict[str, Any]] = {}
        try:
            rows = client.cat.indices(index=pattern, format="json", expand_wildcards=expand)
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict) and row.get("index"):
                        cat_by_name[str(row["index"])] = parse_cat_index_row(row)
        except Exception as e:
            logger.warning("cat.indices failed: %s", e)

        names = sorted(cat_by_name.keys())[:max_ix]
        if not names:
            return []

        index_arg = ",".join(names)
        mappings_body: dict[str, Any] = {}
        settings_body: dict[str, Any] = {}
        alias_body: dict[str, Any] = {}
        try:
            mappings_body = client.indices.get_mapping(index=index_arg, expand_wildcards=expand) or {}
        except Exception as e:
            logger.warning("get_mapping failed: %s", e)
        try:
            settings_body = client.indices.get_settings(index=index_arg, expand_wildcards=expand) or {}
        except Exception as e:
            logger.warning("get_settings failed: %s", e)
        try:
            alias_body = client.indices.get_alias(index=index_arg, expand_wildcards=expand) or {}
        except Exception as e:
            logger.warning("get_alias failed: %s", e)

        per_index_field_caps: dict[str, dict[str, Any]] = {}
        if include_field_caps:
            for name in names:
                try:
                    fc_resp = client.field_caps(index=name, fields="*")
                    if isinstance(fc_resp, dict):
                        per_index_field_caps[name] = fc_resp
                except Exception as e:
                    logger.debug("field_caps for %s failed: %s", name, e)

        out: list[ElasticsearchIndexInfo] = []
        for name in names:
            mblock = mappings_body.get(name, {}) if isinstance(mappings_body, dict) else {}
            mappings = mblock.get("mappings", {}) if isinstance(mblock, dict) else {}
            sblock = settings_body.get(name, {}) if isinstance(settings_body, dict) else {}
            settings = sblock.get("settings", {}) if isinstance(sblock, dict) else {}
            cat = cat_by_name.get(name, {})
            fc = per_index_field_caps.get(name)
            out.append(
                ElasticsearchIndexInfo(
                    name=name,
                    aliases=aliases_for_index(alias_body if isinstance(alias_body, dict) else {}, name),
                    mappings=mappings if isinstance(mappings, dict) else {},
                    settings=settings if isinstance(settings, dict) else {},
                    shard_config=extract_shard_config(settings if isinstance(settings, dict) else {}),
                    health=cat.get("health"),
                    doc_count=cat.get("doc_count"),
                    store_size=cat.get("store_size"),
                    primary_shards=cat.get("primary_shards"),
                    replica_shards=cat.get("replica_shards"),
                    field_caps=fc,
                )
            )
        return out

    def get_data_streams(self) -> list[ElasticsearchDataStreamInfo]:
        client = self._ensure_client()
        max_ds = self._max("max_data_streams", 500)
        pattern = self._index_pattern()
        try:
            body = client.indices.get_data_stream(name=pattern, expand_wildcards=self._expand_wildcards())
        except Exception as e:
            logger.warning("get_data_stream failed: %s", e)
            return []
        streams = body.get("data_streams", []) if isinstance(body, dict) else []
        out: list[ElasticsearchDataStreamInfo] = []
        for item in sorted(streams, key=lambda x: str(x.get("name", "")))[:max_ds]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            if not name:
                continue
            indices = tuple(
                str(i.get("index_name", ""))
                for i in (item.get("indices") or [])
                if isinstance(i, dict) and i.get("index_name")
            )
            out.append(
                ElasticsearchDataStreamInfo(
                    name=name,
                    indices=indices,
                    template=item.get("template"),
                    generation=item.get("generation"),
                    definition=item,
                )
            )
        return out

    def get_component_templates(self) -> list[ElasticsearchComponentTemplateInfo]:
        client = self._ensure_client()
        max_t = self._max("max_component_templates", 500)
        try:
            body = client.cluster.get_component_template()
        except Exception as e:
            logger.warning("get_component_template failed: %s", e)
            return []
        templates = body.get("component_templates", []) if isinstance(body, dict) else []
        out: list[ElasticsearchComponentTemplateInfo] = []
        for item in sorted(templates, key=lambda x: str(x.get("name", "")))[:max_t]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            if not name:
                continue
            comp = item.get("component_template", item)
            template = comp.get("template", comp) if isinstance(comp, dict) else comp
            out.append(
                ElasticsearchComponentTemplateInfo(
                    name=name,
                    template=template if isinstance(template, dict) else {"body": template},
                )
            )
        return out

    def _opensearch_mode(self) -> bool:
        return _as_bool(self._limits.get("opensearch"), False)

    def get_ingest_pipelines(self) -> list[ElasticsearchPipelineInfo]:
        client = self._ensure_client()
        max_p = self._max("max_pipelines", 500)
        try:
            body = client.ingest.get_pipeline()
        except Exception as e:
            logger.warning("get_pipeline failed: %s", e)
            return []
        if not isinstance(body, dict):
            return []
        out: list[ElasticsearchPipelineInfo] = []
        for name in sorted(body.keys())[:max_p]:
            defn = body[name]
            if isinstance(defn, dict):
                out.append(ElasticsearchPipelineInfo(name=str(name), definition=defn))
        return out

    def get_index_templates(self) -> list[ElasticsearchIndexTemplateInfo]:
        client = self._ensure_client()
        max_t = self._max("max_templates", 500)
        out: list[ElasticsearchIndexTemplateInfo] = []
        seen: set[str] = set()

        try:
            body = client.indices.get_index_template()
            templates = body.get("index_templates", []) if isinstance(body, dict) else []
            for item in sorted(templates, key=lambda x: str(x.get("name", ""))):
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                if not name or name in seen:
                    continue
                tpl = item.get("index_template", {})
                if not isinstance(tpl, dict):
                    tpl = {}
                patterns = tpl.get("index_patterns") or []
                if not isinstance(patterns, list):
                    patterns = [patterns]
                composed = tpl.get("composed_of")
                out.append(
                    ElasticsearchIndexTemplateInfo(
                        name=name,
                        index_patterns=tuple(str(p) for p in patterns),
                        priority=tpl.get("priority"),
                        template=tpl.get("template", {}) if isinstance(tpl.get("template"), dict) else {},
                        composed_of=tuple(str(c) for c in composed) if isinstance(composed, list) else None,
                        legacy=False,
                    )
                )
                seen.add(name)
        except Exception as e:
            logger.warning("get_index_template failed: %s", e)

        if len(out) < max_t:
            try:
                legacy_body = client.indices.get_template()
                if isinstance(legacy_body, dict):
                    for name in sorted(legacy_body.keys()):
                        if len(out) >= max_t:
                            break
                        sname = str(name)
                        if sname in seen or sname.startswith("."):
                            continue
                        tpl = legacy_body[name]
                        if not isinstance(tpl, dict):
                            continue
                        patterns = tpl.get("index_patterns") or []
                        if not isinstance(patterns, list):
                            patterns = [patterns]
                        out.append(
                            ElasticsearchIndexTemplateInfo(
                                name=sname,
                                index_patterns=tuple(str(p) for p in patterns),
                                priority=tpl.get("order"),
                                template={
                                    k: tpl[k]
                                    for k in ("settings", "mappings", "aliases")
                                    if k in tpl
                                },
                                composed_of=None,
                                legacy=True,
                            )
                        )
                        seen.add(sname)
            except Exception as e:
                logger.debug("get_template (legacy) skipped: %s", e)

        return out[:max_t]

    def _fetch_ism_policies(self, client: Any) -> dict[str, Any]:
        """OpenSearch Index State Management policies."""
        for path in ("/_plugins/_ism/policies", "/_opendistro/_ism/policies"):
            try:
                resp = client.transport.perform_request("GET", path)
                if isinstance(resp, dict):
                    if "policies" in resp and isinstance(resp["policies"], list):
                        policies: dict[str, Any] = {}
                        for item in resp["policies"]:
                            if not isinstance(item, dict):
                                continue
                            pid = item.get("_id") or item.get("id") or item.get("name")
                            src = item.get("policy")
                            if src is None and isinstance(item.get("_source"), dict):
                                src = item["_source"].get("policy")
                            if pid:
                                policies[str(pid)] = src if isinstance(src, dict) else {"body": src}
                        return policies
                    return {
                        str(k): v for k, v in resp.items() if not str(k).startswith("_")
                    }
            except Exception as e:
                logger.debug("ISM GET %s failed: %s", path, e)
        return {}

    def get_ilm_policies(self) -> list[ElasticsearchIlmPolicyInfo]:
        client = self._ensure_client()
        max_p = self._max("max_ilm_policies", 200)
        policies: dict[str, Any] = {}
        source = "ilm"

        if self._opensearch_mode():
            policies = self._fetch_ism_policies(client)
            source = "ism"
        else:
            try:
                body = client.ilm.get_lifecycle()
                if isinstance(body, dict):
                    policies = body
            except Exception as e:
                logger.warning("ilm.get_lifecycle failed: %s", e)
            if not policies:
                policies = self._fetch_ism_policies(client)
                if policies:
                    source = "ism"

        out: list[ElasticsearchIlmPolicyInfo] = []
        for name in sorted(policies.keys())[:max_p]:
            pol = policies[name]
            if isinstance(pol, dict) and "policy" in pol:
                policy_body = pol["policy"]
            else:
                policy_body = pol
            if not isinstance(policy_body, dict):
                policy_body = {"definition": policy_body}
            out.append(
                ElasticsearchIlmPolicyInfo(
                    name=str(name),
                    policy=policy_body,
                    source=source,
                )
            )
        return out

    def get_search_template_export_diagnostics(self) -> str | None:
        return self._search_template_diagnostics

    def get_snapshot_repositories(self) -> list[ElasticsearchSnapshotRepositoryInfo]:
        client = self._ensure_client()
        max_r = self._max("max_snapshot_repositories", 100)
        try:
            body = client.snapshot.get_repository()
        except Exception as e:
            logger.warning("snapshot.get_repository failed: %s", e)
            return []
        if not isinstance(body, dict):
            return []
        body = filter_snapshot_repositories_by_type(body, self._limits)
        slm_policies: dict[str, Any] | None = None
        try:
            slm_body = client.slm.get_lifecycle()
            if isinstance(slm_body, dict):
                slm_policies = slm_body
        except Exception:
            pass
        out: list[ElasticsearchSnapshotRepositoryInfo] = []
        for name in sorted(body.keys())[:max_r]:
            repo = body[name]
            if not isinstance(repo, dict):
                continue
            out.append(
                normalize_snapshot_repository(str(name), repo, slm_policies=slm_policies)
            )
        return out

    def get_search_templates(self) -> list[ElasticsearchSearchTemplateInfo]:
        client = self._ensure_client()
        max_t = self._max("max_search_templates", 500)
        self._search_template_diagnostics = None
        scripts: dict[str, Any] = {}
        fetch_errors: list[str] = []
        try:
            scripts = client.transport.perform_request("GET", "/_scripts")
        except Exception as e:
            fetch_errors.append(f"GET /_scripts failed: {e}")
            logger.warning("GET /_scripts failed: %s", e)
            try:
                state = client.cluster.state(
                    metric="metadata",
                    filter_path="metadata.stored_scripts",
                )
                meta = state.get("metadata", {}) if isinstance(state, dict) else {}
                scripts = meta.get("stored_scripts", {}) if isinstance(meta, dict) else {}
            except Exception as e2:
                fetch_errors.append(f"cluster.state stored_scripts failed: {e2}")
                logger.warning("cluster.state stored_scripts failed: %s", e2)
                self._search_template_diagnostics = "; ".join(fetch_errors)
                return []

        if not isinstance(scripts, dict):
            self._search_template_diagnostics = "Stored script response was not a mapping."
            return []

        out: list[ElasticsearchSearchTemplateInfo] = []
        for script_id in sorted(scripts.keys())[:max_t]:
            spec = scripts[script_id]
            if not isinstance(spec, dict):
                continue
            normalized = normalize_search_template(str(script_id), spec, self._limits)
            if normalized is not None:
                out.append(normalized)
        if fetch_errors and out:
            self._search_template_diagnostics = (
                "Partial fetch: " + "; ".join(fetch_errors)
            )
        return out
