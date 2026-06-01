from __future__ import annotations

from md_generator.db.core.elasticsearch_format import (
    analyzer_chain_lines,
    field_caps_table_rows,
    flatten_mapping_properties,
    invert_alias_map,
)


def test_flatten_mapping_properties() -> None:
    props = {
        "user": {
            "properties": {
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "age": {"type": "integer"},
            }
        },
        "tag": {"type": "keyword"},
    }
    rows = flatten_mapping_properties(props)
    paths = [p for p, _, _ in rows]
    assert "user.name" in paths
    assert "user.name.keyword" in paths
    assert "tag" in paths


def test_flatten_mapping_properties_complex_types_attributes() -> None:
    props = {
        "parent_child": {"type": "join", "relations": {"question": "answer"}},
        "embedding": {"type": "dense_vector", "dims": 384, "similarity": "cosine"},
        "doc": {
            "type": "nested",
            "dynamic": "strict",
            "properties": {"score": {"type": "float"}},
        },
        "semantic": {"type": "semantic_text", "inference_id": "elser-v2"},
    }
    rows = flatten_mapping_properties(props)
    lookup = {path: (typ, attrs) for path, typ, attrs in rows}
    assert lookup["parent_child"][0] == "join"
    assert "relations=question->answer" in lookup["parent_child"][1]
    assert lookup["embedding"][0] == "dense_vector"
    assert "dims=384" in lookup["embedding"][1]
    assert "similarity=cosine" in lookup["embedding"][1]
    assert lookup["doc"][0] == "nested"
    assert "dynamic=strict" in lookup["doc"][1]
    assert lookup["semantic"][0] == "semantic_text"
    assert "inference_id=elser-v2" in lookup["semantic"][1]


def test_analyzer_chain_lines() -> None:
    analysis = {
        "analyzer": {
            "my_analyzer": {
                "tokenizer": "standard",
                "filter": ["lowercase", "stop"],
            }
        }
    }
    chains = analyzer_chain_lines(analysis)
    assert chains == [("my_analyzer", "standard -> lowercase -> stop")]


def test_field_caps_table_rows() -> None:
    body = {
        "fields": {
            "message": {
                "text": {"type": "text", "searchable": True, "aggregatable": False},
            },
            "@timestamp": {
                "date": {"type": "date", "searchable": True, "aggregatable": True},
            },
        }
    }
    rows = field_caps_table_rows(body)
    assert ("message", "text", "searchable=True, aggregatable=False") in rows
    assert any(r[0] == "@timestamp" for r in rows)


def test_invert_alias_map() -> None:
    body = {
        "logs-2025.01.01": {"aliases": {"logs-current": {}}},
        "logs-2025.01.02": {"aliases": {"logs-current": {}}},
    }
    inv = invert_alias_map(body)
    assert inv["logs-current"] == ["logs-2025.01.01", "logs-2025.01.02"]
