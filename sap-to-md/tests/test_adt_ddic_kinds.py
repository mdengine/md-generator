from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.ddic.adt_parser import AdtDdicParserPlugin
from md_generator.sap.parser.ddic.adt_xml import is_adt_ddic_xml, parse_adt_ddic_file
from md_generator.sap.parser.ddic.ddic_resolver import enrich_ddic_objects_in_run

FIXTURES = Path(__file__).parent / "fixtures" / "ddic"

STRUCT_FIXTURE = FIXTURES / "bal_s_cont.tabl.xml"
TTYP_FIXTURE = FIXTURES / "bal_t_cont.ttyp.xml"
RSDT_FIXTURE = FIXTURES / "char100_range.rsdt.xml"
REFT_FIXTURE = FIXTURES / "char100_ref.reft.xml"
DE_STRUCT_FIXTURE = FIXTURES / "bal_s_cont.dtel.xml"
DTEL_FIXTURE = FIXTURES / "char100.dtel.xml"
DOM_FIXTURE = FIXTURES / "char100.dom.xml"


def test_new_kinds_detected():
    for path in (STRUCT_FIXTURE, TTYP_FIXTURE, RSDT_FIXTURE, REFT_FIXTURE, DE_STRUCT_FIXTURE):
        assert is_adt_ddic_xml(path)


def test_parse_structure():
    parsed = parse_adt_ddic_file(STRUCT_FIXTURE)
    assert parsed is not None
    assert parsed["object_kind"] == "STRUCTURE"
    st = parsed["structure"]
    assert st["name"] == "BAL_S_CONT"
    assert len(st["components"]) == 2
    assert st["components"][0]["name"] == "MSG"
    assert st["components"][0]["data_element"] == "SYCHAR100"


def test_parse_table_type():
    parsed = parse_adt_ddic_file(TTYP_FIXTURE)
    assert parsed is not None
    assert parsed["object_kind"] == "TABLE_TYPE"
    tt = parsed["table_type"]
    assert tt["name"] == "BAL_T_CONT"
    assert tt["row_type"] == "BAL_S_CONT"
    assert tt["line_type"] == "BAL_S_CONT"
    assert tt["access_mode"] == "STANDARD"
    assert tt["primary_key"] == ["MSG"]


def test_parse_range_type():
    parsed = parse_adt_ddic_file(RSDT_FIXTURE)
    assert parsed is not None
    assert parsed["object_kind"] == "RANGE_TYPE"
    rt = parsed["range_type"]
    assert rt["name"] == "CHAR100_RANGE"
    assert rt["data_element"] == "CHAR100"
    assert rt["domain"] == "CHAR100"
    assert rt["length"] == 100


def test_parse_reference_type():
    parsed = parse_adt_ddic_file(REFT_FIXTURE)
    assert parsed is not None
    assert parsed["object_kind"] == "REFERENCE_TYPE"
    rt = parsed["reference_type"]
    assert rt["name"] == "CHAR100_REF"
    assert rt["referenced_type"] == "CHAR100"
    assert rt["check_table"] == "T005"


def test_parse_data_element_structure_type_kind():
    parsed = parse_adt_ddic_file(DE_STRUCT_FIXTURE)
    assert parsed is not None
    de = parsed["data_element"]
    assert de["type_kind"] == "structure"
    assert de["type_name"] == "BAL_S_CONT"


def _parse_all(paths: list[Path]) -> list[SapObject]:
    plugin = AdtDdicParserPlugin()
    ctx = ParseContext(root=FIXTURES)
    objects: list[SapObject] = []
    for path in paths:
        result = plugin.parse(path, ctx)
        objects.extend(result.objects)
    return objects


def test_plugin_kinds():
    cases = [
        (STRUCT_FIXTURE, SapObjectKind.STRUCTURE, "BAL_S_CONT"),
        (TTYP_FIXTURE, SapObjectKind.TABLE_TYPE, "BAL_T_CONT"),
        (RSDT_FIXTURE, SapObjectKind.RANGE_TYPE, "CHAR100_RANGE"),
        (REFT_FIXTURE, SapObjectKind.REFERENCE_TYPE, "CHAR100_REF"),
    ]
    plugin = AdtDdicParserPlugin()
    ctx = ParseContext(root=FIXTURES)
    for path, kind, name in cases:
        obj = plugin.parse(path, ctx).objects[0]
        assert obj.kind == kind
        assert obj.name == name
        assert obj.raw_metadata["adt_ddic"]["ddic_object_kind"] == kind.name


def test_enrich_ddic_resolves_structure_reference():
    objects = _parse_all([DE_STRUCT_FIXTURE, STRUCT_FIXTURE])
    enrich_ddic_objects_in_run(objects)
    de_obj = next(o for o in objects if o.name == "BAL_S_CONT_DE")
    resolved = de_obj.raw_metadata["data_element"]["resolved_type"]
    struct_obj = next(o for o in objects if o.name == "BAL_S_CONT")
    assert resolved["object_id"] == struct_obj.object_id
    assert resolved["ddic_object_kind"] == "STRUCTURE"
    assert resolved["resolution_strategy"] == "same_run_name_match"


def test_normalize_new_kinds_graph_edges():
    normalizer = default_normalizer_registry()
    plugin = AdtDdicParserPlugin()
    ctx = ParseContext(root=FIXTURES)

    struct_obj = plugin.parse(STRUCT_FIXTURE, ctx).objects[0]
    artifact, graph = normalizer.normalize(struct_obj)
    assert artifact is not None
    assert artifact.artifact_type == "ddic.structure"
    assert len(graph.edges) >= 2

    tt_obj = plugin.parse(TTYP_FIXTURE, ctx).objects[0]
    artifact, graph = normalizer.normalize(tt_obj)
    assert artifact.artifact_type == "ddic.table_type"
    assert any(e.relationship.value == "REFERENCES" for e in graph.edges.values())

    rt_obj = plugin.parse(RSDT_FIXTURE, ctx).objects[0]
    artifact, graph = normalizer.normalize(rt_obj)
    assert artifact.artifact_type == "ddic.range_type"
    assert len(graph.edges) >= 2

    ref_obj = plugin.parse(REFT_FIXTURE, ctx).objects[0]
    artifact, graph = normalizer.normalize(ref_obj)
    assert artifact.artifact_type == "ddic.reference_type"
    assert len(graph.edges) >= 2


def test_enrich_domain_data_element():
    objects = _parse_all([DTEL_FIXTURE, DOM_FIXTURE])
    enrich_ddic_objects_in_run(objects)
    de_obj = next(o for o in objects if o.name == "CHAR100" and o.kind == SapObjectKind.DATA_ELEMENT)
    resolved = de_obj.raw_metadata["data_element"]["resolved_type"]
    dom_obj = next(o for o in objects if o.kind == SapObjectKind.DOMAIN)
    assert resolved["object_id"] == dom_obj.object_id
    assert resolved["ddic_object_kind"] == "DOMAIN"
