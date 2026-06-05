from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.parser.ddic.adt_parser import AdtDdicParserPlugin
from md_generator.sap.parser.ddic.adt_xml import is_adt_ddic_xml, parse_adt_ddic_file
from md_generator.sap.parser.base import ParseContext

DTEL_FIXTURE = Path(__file__).parent / "fixtures" / "ddic" / "char100.dtel.xml"
DOM_FIXTURE = Path(__file__).parent / "fixtures" / "ddic" / "char100.dom.xml"


def test_is_adt_ddic_xml():
    assert is_adt_ddic_xml(DTEL_FIXTURE)
    assert is_adt_ddic_xml(DOM_FIXTURE)


def test_parse_data_element():
    parsed = parse_adt_ddic_file(DTEL_FIXTURE)
    assert parsed is not None
    assert parsed["object_kind"] == "DATA_ELEMENT"
    de = parsed["data_element"]
    assert de["name"] == "CHAR100"
    assert de["description"] == "Charakter 100"
    assert de["package"] == "SZS"
    assert de["type_kind"] == "domain"
    assert de["type_name"] == "CHAR100"
    assert de["data_type"] == "CHAR"
    assert de["data_type_length"] == 100


def test_parse_domain():
    parsed = parse_adt_ddic_file(DOM_FIXTURE)
    assert parsed is not None
    assert parsed["object_kind"] == "DOMAIN"
    dom = parsed["domain"]
    assert dom["name"] == "CHAR100"
    assert dom["data_type"] == "CHAR"
    assert dom["length"] == 100


def test_adt_ddic_plugin():
    plugin = AdtDdicParserPlugin()
    assert plugin.can_parse(DTEL_FIXTURE)
    result = plugin.parse(DTEL_FIXTURE, ParseContext(root=DTEL_FIXTURE.parent))
    assert len(result.objects) == 1
    obj = result.objects[0]
    assert obj.kind == SapObjectKind.DATA_ELEMENT
    assert obj.name == "CHAR100"
    assert obj.raw_metadata["data_element"]["data_type"] == "CHAR"


def test_normalize_data_element():
    plugin = AdtDdicParserPlugin()
    result = plugin.parse(DTEL_FIXTURE, ParseContext(root=DTEL_FIXTURE.parent))
    obj = result.objects[0]
    normalizer = default_normalizer_registry()
    artifact, graph = normalizer.normalize(obj)
    assert artifact is not None
    assert artifact.artifact_type == "ddic.data_element"
    assert any(e.relationship.value == "REFERENCES" for e in graph.edges.values())
