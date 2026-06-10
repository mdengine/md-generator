from __future__ import annotations

from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.bapi.parser import BapiParserPlugin
from md_generator.sap.parser.odata.parser import ODataParserPlugin, parse_odata_metadata

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_v4_json_sap_objects():
    p = FIXTURES / "v4_metadata.json"
    result = ODataParserPlugin().parse(p, ParseContext(root=FIXTURES))
    assert any(o.name == "PRODUCT" for o in result.objects)
    assert any(o.kind == SapObjectKind.ODATA_ENTITY_SET for o in result.objects)


def test_bapi_not_odata():
    p = FIXTURES.parent / "bapi" / "bapi_customer.json"
    assert not ODataParserPlugin().can_parse(p)
    assert BapiParserPlugin().can_parse(p)


def test_legacy_api_unchanged():
    service, entities = parse_odata_metadata(FIXTURES / "metadata.xml")
    assert service == "metadata"
    assert any(e["name"] == "Customer" for e in entities)
