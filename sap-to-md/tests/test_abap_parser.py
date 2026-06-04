from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.parser.abap.parser import parse_abap_file
from md_generator.sap.parser.abap.view_resolver import enrich_abap_objects_in_run
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.graph.builder import build_sap_graph
from md_generator.sap.markdown.builders.abap_sections import build_abap_program_markdown

FIXTURE = Path(__file__).parent / "fixtures" / "abap" / "z_customer_sync.abap"
NATIVE_FIXTURE = Path(__file__).parent / "fixtures" / "abap" / "z_hana_native.abap"
GOLDEN = Path(__file__).parent / "golden" / "abap_z_customer_sync.json"


def test_abap_parser_tables_and_auth():
    analysis = parse_abap_file(FIXTURE)
    assert "KNA1" in analysis.tables
    assert "VBAK" in analysis.tables
    assert "ZI_CUSTOMER" in analysis.tables
    assert any(j.table == "VBAK" for j in analysis.joins)
    assert any(j.condition for j in analysis.joins)
    assert "BAPI_CUSTOMER_GETDETAIL" in analysis.functions
    assert any(a.object == "Z_CUST" for a in analysis.auth_checks)
    assert analysis.includes
    assert analysis.validations
    assert len(analysis.sql_statements) >= 2
    assert any(s.source_type == "OPEN_SQL" for s in analysis.sql_statements)
    assert any(r.name == "ZI_CUSTOMER" and r.kind == "cds" for r in analysis.view_references)


def test_abap_native_sql_and_dynamic():
    analysis = parse_abap_file(NATIVE_FIXTURE)
    assert any(s.source_type == "EXEC_SQL" for s in analysis.sql_statements)
    assert any(s.source_type == "ADBC" for s in analysis.sql_statements)
    assert any(s.source_type == "DYNAMIC_SQL" for s in analysis.sql_statements)
    assert analysis.dynamic_sql_signals
    assert analysis.lineage_completeness == "partial"
    refs = {r.name for r in analysis.view_references}
    assert "CV_SALES" in refs or any("CV_SALES" in o for s in analysis.sql_statements for o in s.objects)


def test_abap_sql_fingerprint_and_complexity():
    analysis = parse_abap_file(FIXTURE)
    for stmt in analysis.sql_statements:
        assert stmt.fingerprint
        assert stmt.stable_id.startswith("ABAP::SQL::")
        assert stmt.complexity.join_count >= 0


def test_abap_golden_snapshot():
    analysis = parse_abap_file(FIXTURE)
    data = analysis.to_dict()
    if GOLDEN.exists():
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        assert data["program"] == expected["program"]
        assert set(data["tables"]) >= set(expected["tables"])
        assert set(data["functions"]) == set(expected["functions"])
    else:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_abap_markdown_sections():
    analysis = parse_abap_file(FIXTURE)
    md = build_abap_program_markdown(analysis.program, analysis.to_dict())
    assert "## Open SQL" in md
    assert "## Joins" in md
    assert "ZI_CUSTOMER" in md
    assert "INNER JOIN" in md or "JOIN" in md


def test_abap_graph_resolves_cds_in_run():
    analysis = parse_abap_file(FIXTURE)
    abap_obj = SapObject(
        kind=SapObjectKind.PROGRAM,
        name=analysis.program,
        raw_metadata={"abap": analysis.to_dict()},
    )
    cds_obj = SapObject(
        kind=SapObjectKind.CDS_VIEW,
        name="ZI_CUSTOMER",
        raw_metadata={"cds": {"tables": []}},
    )
    objects = [abap_obj, cds_obj]
    enrich_abap_objects_in_run(objects)
    graph = build_sap_graph(objects)
    edges = list(graph.edges(data=True))
    assert any(e[2].get("view_kind") == "cds" or "ZI_CUSTOMER" in str(e) for e in edges)
