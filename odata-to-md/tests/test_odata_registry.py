from __future__ import annotations

from pathlib import Path

from md_generator.odata.models.domain import ODataFormat, ODataVersion
from md_generator.odata.parser.detector import detect_format, detect_version
from md_generator.odata.parser.registry import get_parser, parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_registry_v2_dispatch():
    fmt = detect_format(FIXTURES / "metadata.xml")
    ver = detect_version(FIXTURES / "metadata.xml", fmt)
    parser = get_parser(ver, fmt)
    doc = parser.parse(FIXTURES / "metadata.xml")
    assert doc.odata_version == ODataVersion.V2
    assert any(e.name == "Customer" for e in doc.entity_types)


def test_registry_v4_json_dispatch():
    fmt = detect_format(FIXTURES / "v4_metadata.json")
    ver = detect_version(FIXTURES / "v4_metadata.json", fmt)
    assert fmt == ODataFormat.CSDL_JSON
    assert ver == ODataVersion.V4
    doc = get_parser(ver, fmt).parse(FIXTURES / "v4_metadata.json")
    assert doc.entity_sets[0].name == "Products"


def test_registry_v4_xml_dispatch():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    assert doc.odata_version == ODataVersion.V4
    assert doc.actions[0].name == "ResetStock"
