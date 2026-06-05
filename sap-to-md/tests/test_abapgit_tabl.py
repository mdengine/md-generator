from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.ddic.abapgit_tabl import (
    is_abapgit_tabl_xml,
    parse_abapgit_tabl_xml,
)
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.ddic.abapgit_tabl import AbapGitTablParserPlugin

FIXTURES = Path(__file__).parent / "fixtures" / "ddic"


def test_abapgit_table_detected():
    path = FIXTURES / "ztest_tab.abapgit.tabl.xml"
    assert is_abapgit_tabl_xml(path)


def test_abapgit_table_parse():
    parsed = parse_abapgit_tabl_xml((FIXTURES / "ztest_tab.abapgit.tabl.xml").read_text(encoding="utf-8"))
    assert parsed is not None
    assert parsed["object_kind"] == "TABLE"
    ddic = parsed["ddic"]
    assert ddic["name"] == "ZTEST_TAB"
    assert len(ddic["fields"]) == 2


def test_abapgit_structure_parse():
    parsed = parse_abapgit_tabl_xml((FIXTURES / "ztest_str.abapgit.tabl.xml").read_text(encoding="utf-8"))
    assert parsed is not None
    assert parsed["object_kind"] == "STRUCTURE"
    st = parsed["structure"]
    assert st["name"] == "ZTEST_STR"
    assert len(st["components"]) == 1


def test_abapgit_plugin():
    plugin = AbapGitTablParserPlugin()
    path = FIXTURES / "ztest_tab.abapgit.tabl.xml"
    assert plugin.can_parse(path)
    result = plugin.parse(path, ParseContext(root=FIXTURES))
    assert len(result.objects) == 1
    assert result.objects[0].kind == SapObjectKind.TABLE
