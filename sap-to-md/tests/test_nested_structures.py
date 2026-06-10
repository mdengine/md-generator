from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.ddic.adt_parser import AdtDdicParserPlugin
from md_generator.sap.parser.ddic.adt_xml import parse_adt_ddic_file
from md_generator.sap.parser.ddic.ddic_resolver import expand_nested_structures

FIXTURES = Path(__file__).parent / "fixtures" / "ddic"


def _parse_objects(*names: str) -> list[SapObject]:
    plugin = AdtDdicParserPlugin()
    ctx = ParseContext(root=FIXTURES)
    objects: list[SapObject] = []
    for name in names:
        result = plugin.parse(FIXTURES / name, ctx)
        objects.extend(result.objects)
    return objects


def test_nested_include_expansion():
    objects = _parse_objects("bal_s_cont.tabl.xml", "bal_s_cont_include.tabl.xml")
    expand_nested_structures(objects)
    hdr = next(o for o in objects if o.name == "BAL_S_HDR")
    meta = hdr.raw_metadata["structure"]
    cont = next(c for c in meta["components"] if c["name"] == "CONT")
    assert cont["type_kind"] == "structure"
    assert cont["type_name"] == "BAL_S_CONT"
    assert len(cont["children"]) == 2
    assert cont["children"][0]["name"] == "MSG"


def test_circular_include_detected():
    objects = _parse_objects("z_circular_a.tabl.xml", "z_circular_b.tabl.xml")
    expand_nested_structures(objects)
    a = next(o for o in objects if o.name == "Z_CIRC_A")

    def _has_cycle(comps: list[dict]) -> bool:
        for comp in comps:
            if comp.get("cycle_detected"):
                return True
            if _has_cycle(comp.get("children") or []):
                return True
        return False

    assert _has_cycle(a.raw_metadata["structure"]["components"])


def test_blue_source_ddl_sidecar():
    parsed = parse_adt_ddic_file(FIXTURES / "t005_blue_source.tabl.xml")
    assert parsed is not None
    ddic = parsed["ddic"]
    assert ddic["definition_source"] == "adt_ddl_sidecar"
    assert len(ddic["fields"]) >= 2
