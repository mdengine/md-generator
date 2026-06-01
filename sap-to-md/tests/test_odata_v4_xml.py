from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.metadata.odata import ODataVersion
from md_generator.sap.parser.odata.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_v4_xml_entity_set():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    assert doc.odata_version == ODataVersion.V4
    assert len(doc.entity_sets) == 1
    assert doc.entity_sets[0].name == "Products"


def test_v4_xml_capabilities():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    cap = doc.entity_sets[0].capabilities
    assert cap.insertable is True
    assert cap.deletable is False
    assert cap.searchable is True


def test_v4_xml_actions_functions():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    assert any(a.name == "ResetStock" for a in doc.actions)
    assert any(f.name == "GetStock" for f in doc.functions)


def test_v4_xml_nav_collection_multiplicity():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    product = next(e for e in doc.entity_types if e.name == "Product")
    nav = product.navigation_properties[0]
    assert nav.name == "Details"
    assert nav.multiplicity == "n"
