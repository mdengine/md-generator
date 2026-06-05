from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.markdown.builders.entity_builder import build_entity_markdown
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.ddic.adt_parser import AdtDdicParserPlugin
from md_generator.sap.parser.cds.parser import CdsParserPlugin

FIXTURES = Path(__file__).parent / "fixtures" / "ddic"
CDS_FIXTURES = Path(__file__).parent / "fixtures" / "cds"


def _entity_md(fixture: Path) -> str:
    plugin = AdtDdicParserPlugin()
    obj = plugin.parse(fixture, ParseContext(root=fixture.parent)).objects[0]
    return build_entity_markdown(obj)


def test_entity_md_data_element():
    md = _entity_md(FIXTURES / "char100.dtel.xml")
    assert "## DDIC Data Element" in md
    assert "Type kind" in md
    assert "CHAR100" in md


def test_entity_md_domain():
    md = _entity_md(FIXTURES / "char100.dom.xml")
    assert "## DDIC Domain" in md
    assert "Data type" in md


def test_entity_md_structure():
    md = _entity_md(FIXTURES / "bal_s_cont.tabl.xml")
    assert "## Structure" in md
    assert "Definition source" in md
    assert "MSG" in md


def test_entity_md_table_type():
    md = _entity_md(FIXTURES / "bal_t_cont.ttyp.xml")
    assert "## DDIC Table Type" in md
    assert "Row type" in md


def test_entity_md_range_type():
    md = _entity_md(FIXTURES / "char100_range.rsdt.xml")
    assert "## DDIC Range Type" in md


def test_entity_md_reference_type():
    md = _entity_md(FIXTURES / "char100_ref.reft.xml")
    assert "## DDIC Reference Type" in md


def test_entity_md_cds_structure():
    plugin = CdsParserPlugin()
    obj = plugin.parse(CDS_FIXTURES / "bal_s_msg.ddls", ParseContext(root=CDS_FIXTURES)).objects[0]
    assert obj.kind == SapObjectKind.CDS_STRUCTURE
    md = build_entity_markdown(obj)
    assert "## Structure" in md
    assert "cds_ddl" in md
    assert "MSGTY" in md


def test_technical_metadata_shows_ddic_kind():
    md = _entity_md(FIXTURES / "char100.dtel.xml")
    assert "DDIC object kind" in md or "data_element" in md
