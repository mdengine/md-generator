"""Pure helpers for Elasticsearch mapping / analyzer presentation."""

from __future__ import annotations

from typing import Any


def index_pattern_from_limits(limits: dict[str, Any]) -> str:
    p = limits.get("index_pattern")
    if p is None or str(p).strip() == "":
        return "*"
    return str(p).strip()


def extract_shard_config(settings_block: dict[str, Any]) -> dict[str, Any]:
    """Normalize shard-related settings from an index settings dict."""
    idx = settings_block
    if "index" in settings_block and isinstance(settings_block["index"], dict):
        idx = settings_block["index"]
    keys = (
        "number_of_shards",
        "number_of_replicas",
        "routing_partition_size",
        "codec",
        "refresh_interval",
    )
    out: dict[str, Any] = {}
    for k in keys:
        v = idx.get(k)
        if v is not None:
            out[k] = v
    return out


def extract_analysis(settings_block: dict[str, Any]) -> dict[str, Any]:
    idx = settings_block
    if "index" in settings_block and isinstance(settings_block["index"], dict):
        idx = settings_block["index"]
    analysis = idx.get("analysis")
    return dict(analysis) if isinstance(analysis, dict) else {}


def settings_without_analysis(settings_block: dict[str, Any]) -> dict[str, Any]:
    """Copy settings with ``index.analysis`` removed (for separate sections)."""
    import copy

    s = copy.deepcopy(settings_block)
    if isinstance(s.get("index"), dict) and "analysis" in s["index"]:
        s["index"] = {k: v for k, v in s["index"].items() if k != "analysis"}
    return s


def _mapping_attributes(spec: dict[str, Any], ftype: str) -> str:
    """Return a compact attributes string for complex Elasticsearch field types."""
    attrs: list[str] = []
    if ftype in ("nested", "object"):
        if "dynamic" in spec:
            attrs.append(f"dynamic={spec.get('dynamic')}")
        if "enabled" in spec:
            attrs.append(f"enabled={spec.get('enabled')}")
    if ftype == "join":
        rel = spec.get("relations")
        if isinstance(rel, dict):
            pairs = []
            for parent in sorted(rel.keys()):
                child = rel[parent]
                if isinstance(child, list):
                    pairs.append(f"{parent}->{','.join(str(x) for x in child)}")
                else:
                    pairs.append(f"{parent}->{child}")
            if pairs:
                attrs.append("relations=" + ";".join(pairs))
    if ftype in ("dense_vector", "sparse_vector"):
        for key in ("dims", "index", "similarity", "element_type"):
            if key in spec:
                attrs.append(f"{key}={spec.get(key)}")
    if ftype == "semantic_text":
        for key in ("inference_id", "model_id", "search_inference_id"):
            if key in spec:
                attrs.append(f"{key}={spec.get(key)}")
    if ftype == "flattened":
        for key in ("depth_limit", "ignore_above"):
            if key in spec:
                attrs.append(f"{key}={spec.get(key)}")
    return ", ".join(attrs)


def flatten_mapping_properties(
    properties: dict[str, Any], prefix: str = ""
) -> list[tuple[str, str, str]]:
    """Yield (field_path, type, attributes) rows from mappings ``properties``."""
    rows: list[tuple[str, str, str]] = []

    def walk(props: dict[str, Any], pfx: str) -> None:
        for name in sorted(props.keys()):
            spec = props[name]
            if not isinstance(spec, dict):
                continue
            path = f"{pfx}.{name}" if pfx else name
            ftype = spec.get("type")
            if ftype == "nested" and isinstance(spec.get("properties"), dict):
                rows.append((path, "nested", _mapping_attributes(spec, "nested")))
                walk(spec["properties"], path)
                continue
            if isinstance(spec.get("properties"), dict):
                ftype_out = str(ftype or "object")
                rows.append((path, ftype_out, _mapping_attributes(spec, ftype_out)))
                walk(spec["properties"], path)
            elif ftype:
                ftype_out = str(ftype)
                rows.append((path, ftype_out, _mapping_attributes(spec, ftype_out)))
                if isinstance(spec.get("fields"), dict):
                    for sub, sub_spec in sorted(spec["fields"].items()):
                        if isinstance(sub_spec, dict):
                            sub_type = str(sub_spec.get("type", "object"))
                            rows.append(
                                (
                                    f"{path}.{sub}",
                                    sub_type,
                                    _mapping_attributes(sub_spec, sub_type),
                                )
                            )
            else:
                rows.append((path, "object", _mapping_attributes(spec, "object")))

    walk(properties, prefix)
    return rows


def summarize_mapping_properties(properties: dict[str, Any]) -> dict[str, Any]:
    rows = flatten_mapping_properties(properties)
    by_type: dict[str, int] = {}
    for _, t, _ in rows:
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "field_count": len(rows),
        "types": dict(sorted(by_type.items())),
    }


def analyzer_chain_lines(analysis: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (analyzer_name, chain_text) for each custom analyzer."""
    analyzers = analysis.get("analyzer") or {}
    tokenizers = analysis.get("tokenizer") or {}
    lines: list[tuple[str, str]] = []
    if not isinstance(analyzers, dict):
        return lines
    for name in sorted(analyzers.keys()):
        spec = analyzers[name]
        if not isinstance(spec, dict):
            continue
        parts: list[str] = []
        tok = spec.get("tokenizer")
        if tok:
            parts.append(str(tok))
        for flt in spec.get("filter") or []:
            parts.append(str(flt))
        for ch in spec.get("char_filter") or []:
            parts.insert(0, str(ch))
        if not parts and name in tokenizers:
            parts.append(name)
        chain = " -> ".join(parts) if parts else "(default / builtin)"
        lines.append((name, chain))
    return lines


def parse_cat_index_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a ``cat.indices`` JSON row."""
    def _int(key: str) -> int | None:
        v = row.get(key)
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    return {
        "health": row.get("health"),
        "doc_count": _int("docs.count") or _int("docs_count"),
        "store_size": row.get("store.size") or row.get("store_size"),
        "primary_shards": _int("pri"),
        "replica_shards": _int("rep"),
    }


def aliases_for_index(alias_response: dict[str, Any], index_name: str) -> tuple[str, ...]:
    """Extract alias names pointing at ``index_name`` from ``indices.get_alias`` body."""
    names: list[str] = []
    block = alias_response.get(index_name) or {}
    aliases = block.get("aliases") or {}
    if isinstance(aliases, dict):
        names.extend(sorted(aliases.keys()))
    return tuple(names)


def field_caps_table_rows(field_caps_response: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Parse ``field_caps`` API body into (field, type, capabilities) rows."""
    fields = field_caps_response.get("fields")
    if not isinstance(fields, dict):
        return []
    rows: list[tuple[str, str, str]] = []
    for field_name in sorted(fields.keys()):
        types_block = fields[field_name]
        if not isinstance(types_block, dict):
            continue
        for type_name in sorted(types_block.keys()):
            meta = types_block[type_name]
            if not isinstance(meta, dict):
                rows.append((field_name, str(type_name), ""))
                continue
            caps: list[str] = []
            for key in ("searchable", "aggregatable", "indices"):
                if key in meta:
                    caps.append(f"{key}={meta[key]}")
            rows.append((field_name, str(type_name), ", ".join(caps)))
    return rows


def invert_alias_map(alias_response: dict[str, Any]) -> dict[str, list[str]]:
    """alias -> [index names]."""
    out: dict[str, list[str]] = {}
    for index_name, block in sorted(alias_response.items()):
        if not isinstance(block, dict):
            continue
        for alias_name in (block.get("aliases") or {}):
            out.setdefault(alias_name, []).append(index_name)
    for k in out:
        out[k] = sorted(out[k])
    return out
