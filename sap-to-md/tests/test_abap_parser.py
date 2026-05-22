from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.parser.abap.parser import parse_abap_file

FIXTURE = Path(__file__).parent / "fixtures" / "abap" / "z_customer_sync.abap"
GOLDEN = Path(__file__).parent / "golden" / "abap_z_customer_sync.json"


def test_abap_parser_tables_and_auth():
    analysis = parse_abap_file(FIXTURE)
    assert "KNA1" in analysis.tables
    assert "VBAK" in analysis.tables
    assert any(j.table == "VBAK" for j in analysis.joins)
    assert "BAPI_CUSTOMER_GETDETAIL" in analysis.functions
    assert any(a.object == "Z_CUST" for a in analysis.auth_checks)
    assert analysis.includes
    assert analysis.validations


def test_abap_golden_snapshot():
    analysis = parse_abap_file(FIXTURE)
    data = analysis.to_dict()
    if GOLDEN.exists():
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        assert data["program"] == expected["program"]
        assert set(data["tables"]) == set(expected["tables"])
        assert set(data["functions"]) == set(expected["functions"])
    else:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(data, indent=2), encoding="utf-8")
