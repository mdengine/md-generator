from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.cds.parser import parse_cds_source

FIXTURE = Path(__file__).parent / "fixtures" / "cds" / "zi_customer.ddls"


def test_cds_semantic_entity():
    analysis = parse_cds_source(FIXTURE.read_text(encoding="utf-8"), "zi_customer")
    assert analysis.view_name == "ZI_CUSTOMER"
    assert analysis.semantic_entity == "Customer"
    assert analysis.associations
    assert any("businessobject" in k.lower() for k in analysis.annotations)
