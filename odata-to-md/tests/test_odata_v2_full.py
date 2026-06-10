from __future__ import annotations

from pathlib import Path

from md_generator.odata.parser.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"
GOLDEN = Path(__file__).parent / "golden" / "odata_v2_full.json"


def test_v2_golden_matches_fixture():
    import json

    doc = parse_document(FIXTURES / "v2_with_container.xml")
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = doc.to_dict()
    actual["metadata_url"] = "FIXTURE"
    assert actual["entity_sets"][0]["name"] == expected["entity_sets"][0]["name"]
    assert len(actual["entity_types"]) == len(expected["entity_types"])


def test_entity_sets_on_document():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    assert len(doc.entity_sets) == 2
    assert doc.container_name == "Container"


def test_complex_types_stay_in_analysis():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    assert len(doc.complex_types) == 1
    assert len(doc.enum_types) == 1
    assert any(e.name == "Product" for e in doc.entity_types)
