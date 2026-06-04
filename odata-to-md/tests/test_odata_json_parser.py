from __future__ import annotations

from pathlib import Path

from md_generator.odata.parser.legacy import document_to_legacy_entities
from md_generator.odata.parser.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_v4_json_parser():
    doc = parse_document(FIXTURES / "v4_metadata.json")
    assert any(e.name == "Product" for e in doc.entity_types)
    assert len(doc.entity_sets) == 1
    assert doc.entity_sets[0].name == "Products"


def test_legacy_entity_dict():
    doc = parse_document(FIXTURES / "metadata.xml")
    entities = document_to_legacy_entities(doc)
    assert any(e["name"] == "Customer" for e in entities)
