from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.cds.parser import CdsParserPlugin
from md_generator.sap.parser.cds.table_ddl import is_cds_table_ddl, parse_cds_table_ddl

T005_FIXTURE = Path(__file__).parent / "fixtures" / "cds" / "t005.ddls"
VIEW_FIXTURE = Path(__file__).parent / "fixtures" / "cds" / "zi_customer.ddls"


def test_is_cds_table_ddl():
    assert is_cds_table_ddl(T005_FIXTURE.read_text(encoding="utf-8"))
    assert not is_cds_table_ddl(VIEW_FIXTURE.read_text(encoding="utf-8"))


def test_parse_t005_fields_and_keys():
    tbl = parse_cds_table_ddl(T005_FIXTURE.read_text(encoding="utf-8"), "t005")
    assert tbl.name == "T005"
    assert tbl.table_type == "TRANSPARENT"
    assert tbl.definition_source == "cds_ddl"
    assert "MANDT" in tbl.primary_key
    assert "LAND1" in tbl.primary_key
    assert len(tbl.fields) == 43

    land1 = next(f for f in tbl.fields if f.name == "LAND1")
    assert land1.key is True
    assert land1.data_element == "LAND1"

    mandt = next(f for f in tbl.fields if f.name == "MANDT")
    assert mandt.key is True
    assert mandt.data_element == "MANDT"

    prplz = next(f for f in tbl.fields if f.name == "PRPLZ")
    assert prplz.key is False
    assert prplz.data_element == "PRUEF_005"


def test_cds_plugin_emits_table_object():
    plugin = CdsParserPlugin()
    assert plugin.can_parse(T005_FIXTURE)
    result = plugin.parse(T005_FIXTURE, ParseContext(root=T005_FIXTURE.parent))
    assert len(result.objects) == 1
    obj = result.objects[0]
    assert obj.kind == SapObjectKind.TABLE
    assert obj.name == "T005"
    assert obj.tags == ["ddic", "table", "cds_ddl"]
    ddic = obj.raw_metadata["ddic"]
    assert ddic["table_type"] == "TRANSPARENT"
    assert ddic["definition_source"] == "cds_ddl"
    assert len(ddic["fields"]) == 43


def test_cds_plugin_still_parses_views():
    plugin = CdsParserPlugin()
    result = plugin.parse(VIEW_FIXTURE, ParseContext(root=VIEW_FIXTURE.parent))
    assert result.objects[0].kind == SapObjectKind.CDS_VIEW
