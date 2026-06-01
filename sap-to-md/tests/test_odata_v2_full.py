from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.odata.document_to_objects import document_to_sap_objects
from md_generator.sap.parser.odata.parser import ODataParserPlugin
from md_generator.sap.parser.odata.registry import parse_document

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


def test_entity_sets_emitted():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    result = ODataParserPlugin().parse(FIXTURES / "v2_with_container.xml", ParseContext(root=FIXTURES))
    kinds = {o.kind for o in result.objects}
    assert SapObjectKind.ODATA_ENTITY_SET in kinds
    assert SapObjectKind.ODATA_SERVICE in kinds


def test_complex_types_not_sap_objects():
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    objects = document_to_sap_objects(doc, FIXTURES / "v4_metadata.xml")
    kinds = {o.kind for o in objects}
    assert SapObjectKind.ODATA_ENTITY in kinds
    assert not any(k.value.endswith("COMPLEX") for k in kinds)
    assert len(doc.complex_types) == 1
