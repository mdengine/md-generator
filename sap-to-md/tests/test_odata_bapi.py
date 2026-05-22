from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.bapi.parser import BapiParserPlugin
from md_generator.sap.parser.odata.parser import ODataParserPlugin

FIXTURES = Path(__file__).parent / "fixtures"


def test_odata_parser():
    p = FIXTURES / "odata" / "metadata.xml"
    result = ODataParserPlugin().parse(p, ParseContext(root=FIXTURES))
    assert any(o.name == "CUSTOMER" for o in result.objects)


def test_bapi_parser():
    p = FIXTURES / "bapi" / "bapi_customer.json"
    result = BapiParserPlugin().parse(p, ParseContext(root=FIXTURES))
    assert result.objects[0].name == "BAPI_CUSTOMER_GETDETAIL"
