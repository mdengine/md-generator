from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.ddic.parser import parse_ddic_csv

FIXTURE = Path(__file__).parent / "fixtures" / "ddic" / "dd03l_sample.csv"


def test_ddic_fields():
    tables = parse_ddic_csv(FIXTURE)
    assert len(tables) == 1
    tbl = tables[0]
    assert tbl.name == "KNA1"
    assert "KUNNR" in tbl.primary_key
    email = next(f for f in tbl.fields if f.name == "EMAIL")
    assert email.business_name
