from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.cds.parser import CdsParserPlugin
from md_generator.sap.parser.cds.type_ddl import is_cds_type_ddl, parse_cds_type_ddl

BAL_FIXTURE = Path(__file__).parent / "fixtures" / "cds" / "bal_s_msg.ddls"
TABLE_FIXTURE = Path(__file__).parent / "fixtures" / "cds" / "t005.ddls"
VIEW_FIXTURE = Path(__file__).parent / "fixtures" / "cds" / "zi_customer.ddls"


def test_is_cds_type_ddl():
    assert is_cds_type_ddl(BAL_FIXTURE.read_text(encoding="utf-8"))
    assert not is_cds_type_ddl(TABLE_FIXTURE.read_text(encoding="utf-8"))
    assert not is_cds_type_ddl(VIEW_FIXTURE.read_text(encoding="utf-8"))


def test_parse_bal_s_msg():
    st = parse_cds_type_ddl(BAL_FIXTURE.read_text(encoding="utf-8"), "bal_s_msg")
    assert st.name == "BAL_S_MSG"
    assert st.description == "Anwendungs-Log: Daten einer Meldung"
    assert st.enhancement_category == "NOT_CLASSIFIED"
    assert len(st.components) == 18

    msgty = next(c for c in st.components if c.name == "MSGTY")
    assert msgty.type_name == "SYMSGTY"
    assert msgty.type_kind == "builtin"

    context = next(c for c in st.components if c.name == "CONTEXT")
    assert context.type_name == "BAL_S_CONT"
    assert context.type_kind == "structure"

    params = next(c for c in st.components if c.name == "PARAMS")
    assert params.type_name == "BAL_S_PARM"
    assert params.type_kind == "structure"


def test_cds_plugin_emits_structure():
    plugin = CdsParserPlugin()
    result = plugin.parse(BAL_FIXTURE, ParseContext(root=BAL_FIXTURE.parent))
    obj = result.objects[0]
    assert obj.kind == SapObjectKind.CDS_STRUCTURE
    assert obj.name == "BAL_S_MSG"
    assert obj.description == "Anwendungs-Log: Daten einer Meldung"
    assert obj.tags == ["cds", "structure", "cds_ddl"]


def test_normalize_cds_structure_graph():
    plugin = CdsParserPlugin()
    obj = plugin.parse(BAL_FIXTURE, ParseContext(root=BAL_FIXTURE.parent)).objects[0]
    artifact, graph = default_normalizer_registry().normalize(obj)
    assert artifact is not None
    assert artifact.artifact_type == "cds.structure"
    assert any(e.relationship == RelationshipType.CONTAINS for e in graph.edges.values())
