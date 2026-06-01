"""Search-template query type classification for Elasticsearch exports."""

from __future__ import annotations

import json
from typing import Any

FULL_TEXT = "FULL_TEXT"
AGGREGATION = "AGGREGATION"
SUGGEST = "SUGGEST"
VECTOR_SEARCH = "VECTOR_SEARCH"
SEMANTIC_SEARCH = "SEMANTIC_SEARCH"
HYBRID_SEARCH = "HYBRID_SEARCH"

QUERY_TYPE_LABELS: dict[str, str] = {
    FULL_TEXT: "Full text",
    AGGREGATION: "Aggregation",
    SUGGEST: "Suggest",
    VECTOR_SEARCH: "Vector search",
    SEMANTIC_SEARCH: "Semantic search",
    HYBRID_SEARCH: "Hybrid search",
}

_LEXICAL_KEYS = frozenset(
    {
        "match",
        "multi_match",
        "query_string",
        "simple_query_string",
        "match_phrase",
        "match_phrase_prefix",
        "term",
        "terms",
        "bool",
        "dis_max",
        "intervals",
    }
)


def _parse_query_body(source: Any) -> Any | None:
    if source is None:
        return None
    if isinstance(source, dict):
        return source
    if isinstance(source, str):
        text = source.strip()
        if not text:
            return None
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                return parsed if isinstance(parsed, (dict, list)) else None
            except json.JSONDecodeError:
                return None
        return None
    return None


def _collect_keys(obj: Any, found: set[str], *, depth: int = 0) -> None:
    if depth > 24:
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            found.add(str(key).lower())
            _collect_keys(value, found, depth=depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, found, depth=depth + 1)


def classify_query_source(source: Any) -> tuple[str, ...]:
    """Return stable query-type codes for a template script source."""
    parsed = _parse_query_body(source)
    if parsed is None:
        return ()

    keys: set[str] = set()
    _collect_keys(parsed, keys)
    try:
        text_blob = json.dumps(parsed).lower()
    except (TypeError, ValueError):
        text_blob = str(parsed).lower()

    has_agg = "aggs" in keys or "aggregations" in keys
    has_suggest = "suggest" in keys
    has_knn = "knn" in keys
    has_query = "query" in keys
    has_semantic_key = "semantic" in keys or "semantic_query" in keys
    has_semantic_text = "semantic_text" in text_blob or "inference_id" in text_blob
    has_rank = "rank" in keys
    has_vector = (
        has_knn
        or "dense_vector" in text_blob
        or "sparse_vector" in text_blob
        or "knn_query" in text_blob
    )
    has_lexical = bool(keys & _LEXICAL_KEYS)
    has_semantic = has_semantic_key or has_semantic_text or (has_rank and "semantic" in text_blob)

    types: list[str] = []
    if has_agg:
        types.append(AGGREGATION)
    if has_suggest:
        types.append(SUGGEST)

    if (has_vector or has_semantic) and has_lexical:
        types.append(HYBRID_SEARCH)
    elif has_semantic and not has_vector:
        types.append(SEMANTIC_SEARCH)
    elif has_vector:
        types.append(VECTOR_SEARCH)
    elif has_lexical or has_query:
        types.append(FULL_TEXT)

    return tuple(dict.fromkeys(types))


def classify_search_template_spec(spec: dict[str, Any]) -> tuple[str, ...]:
    if not isinstance(spec, dict):
        return ()
    source = spec.get("source")
    if source is None:
        script = spec.get("script")
        if isinstance(script, dict):
            source = script.get("source")
    return classify_query_source(source)


def format_query_type_heading(query_types: tuple[str, ...]) -> str:
    if not query_types:
        return "_Classification unavailable (dynamic template or unparseable source)._"
    if HYBRID_SEARCH in query_types:
        parts = [QUERY_TYPE_LABELS[t] for t in query_types if t != HYBRID_SEARCH]
        if parts:
            return f"Hybrid search ({' + '.join(parts)})"
        return QUERY_TYPE_LABELS[HYBRID_SEARCH]
    return " + ".join(QUERY_TYPE_LABELS[t] for t in query_types)


def query_type_counts(templates: list[tuple[str, tuple[str, ...]]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, types in templates:
        for t in types:
            counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items()))
