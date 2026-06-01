from __future__ import annotations

from md_generator.db.core.elasticsearch_query_classify import (
    AGGREGATION,
    FULL_TEXT,
    HYBRID_SEARCH,
    SEMANTIC_SEARCH,
    SUGGEST,
    VECTOR_SEARCH,
    classify_query_source,
    classify_search_template_spec,
    format_query_type_heading,
    query_type_counts,
)


def test_classify_full_text_query() -> None:
    types = classify_query_source({"query": {"match": {"message": "{{q}}"}}})
    assert FULL_TEXT in types
    assert VECTOR_SEARCH not in types


def test_classify_aggregation_query() -> None:
    types = classify_query_source({"size": 0, "aggs": {"by_status": {"terms": {"field": "status"}}}})
    assert AGGREGATION in types


def test_classify_vector_search_knn() -> None:
    types = classify_query_source(
        {
            "knn": {
                "field": "embedding",
                "query_vector": [0.1, 0.2],
                "k": 10,
            }
        }
    )
    assert types == (VECTOR_SEARCH,)


def test_classify_hybrid_search() -> None:
    types = classify_query_source(
        {
            "query": {"match": {"text": "{{q}}"}},
            "knn": {"field": "embedding", "query_vector": [0.1], "k": 5},
        }
    )
    assert HYBRID_SEARCH in types


def test_classify_semantic_search() -> None:
    types = classify_query_source(
        {
            "query": {
                "semantic": {
                    "field": "content",
                    "query": "{{q}}",
                }
            }
        }
    )
    assert SEMANTIC_SEARCH in types


def test_classify_suggest() -> None:
    types = classify_query_source({"suggest": {"my-suggest": {"text": "elastic", "term": {"field": "body"}}}})
    assert SUGGEST in types


def test_classify_unparseable_mustache_returns_empty() -> None:
    types = classify_query_source('{"query": {"match": {"x": "{{dynamic_field}}"}}}')
    assert types == (FULL_TEXT,)


def test_classify_invalid_json_string_returns_empty() -> None:
    assert classify_query_source("not-json {{var}}") == ()


def test_classify_nested_script_source() -> None:
    spec = {
        "lang": "mustache",
        "script": {"source": {"knn": {"field": "v", "query_vector": [], "k": 1}}},
    }
    assert VECTOR_SEARCH in classify_search_template_spec(spec)


def test_format_query_type_heading_hybrid() -> None:
    label = format_query_type_heading((HYBRID_SEARCH, FULL_TEXT, VECTOR_SEARCH))
    assert label.startswith("Hybrid search")
    assert "Full text" in label


def test_format_query_type_heading_unavailable() -> None:
    assert "unavailable" in format_query_type_heading(()).lower()


def test_query_type_counts() -> None:
    counts = query_type_counts(
        [
            ("a", (VECTOR_SEARCH,)),
            ("b", (HYBRID_SEARCH, FULL_TEXT)),
            ("c", ()),
        ]
    )
    assert counts[VECTOR_SEARCH] == 1
    assert counts[HYBRID_SEARCH] == 1
    assert counts[FULL_TEXT] == 1
