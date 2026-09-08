from __future__ import annotations

from pathlib import Path
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.graph.builder import build_sap_graph
from md_generator.sap.graph.taxonomy import RelationshipType


def test_abap_sql_graph_nodes():
    # Construct mock raw_metadata for an ABAP program with an Open SQL statement
    abap_meta = {
        "program": "ZTEST_PROG",
        "sql_statements": [
            {
                "statement_kind": "SELECT",
                "source_type": "OPEN_SQL",
                "text": "SELECT * FROM mara INTO TABLE @data(lt_mara).",
                "line": 42,
                "objects": ["MARA"],
                "fingerprint": "select_mara_fingerprint",
                "confidence": 1.0,
                "dynamic_sql_risk": False,
                "complexity": {"complexity_score": 3.0},
            }
        ],
        "tables": ["MARA"],
        "view_references": [
            {
                "name": "MARA",
                "kind": "ddic_table",
                "confidence": 1.0,
                "source_sql_line": 42,
                "resolution": {
                    "resolved_stable_id": "DDIC::MARA",
                    "resolution_strategy": "exact_match",
                },
            }
        ],
    }

    obj = SapObject(
        kind=SapObjectKind.PROGRAM,
        name="ZTEST_PROG",
        package="ZTEST",
        source_path=Path("ztest_prog.abap"),
        raw_metadata={"abap": abap_meta},
    )

    # 1. Test canonical normalization graph fragment
    reg = default_normalizer_registry()
    artifact, fragment = reg.normalize(obj)

    # Verify SQL statement node is created
    stmt_id = "SQL::PROGRAM:ZTEST:ZTEST_PROG::select_m::42"
    assert stmt_id in fragment.nodes
    stmt_node = fragment.nodes[stmt_id]
    assert stmt_node.node_kind == "sql_statement"
    assert stmt_node.namespace == "ABAP::SQL"
    assert stmt_node.properties["fingerprint"] == "select_mara_fingerprint"
    assert stmt_node.properties["complexity_score"] == 3.0

    # Verify program --EXECUTES--> SQLStatement edge
    exec_edge_id = "PROGRAM:ZTEST:ZTEST_PROG->executes->SQL::PROGRAM:ZTEST:ZTEST_PROG::select_m::42"
    assert exec_edge_id in fragment.edges
    exec_edge = fragment.edges[exec_edge_id]
    assert exec_edge.relationship == RelationshipType.EXECUTES

    # Verify SQLStatement --READS_FROM--> MARA edge (resolved to DDIC::MARA)
    reads_edge_id = "SQL::PROGRAM:ZTEST:ZTEST_PROG::select_m::42->reads->DDIC::MARA"
    assert reads_edge_id in fragment.edges
    reads_edge = fragment.edges[reads_edge_id]
    assert reads_edge.relationship == RelationshipType.READS_FROM
    assert reads_edge.properties["confidence"] == 1.0

    # 2. Test NetworkX v1 graph building
    table_obj = SapObject(
        kind=SapObjectKind.TABLE,
        name="MARA",
        package="ZTEST",
    )
    g = build_sap_graph([obj, table_obj])
    prog_node_id = "PROGRAM:ZTEST:ZTEST_PROG"
    assert prog_node_id in g
    assert stmt_id in g

    # Verify edges in NetworkX
    assert g.has_edge(prog_node_id, stmt_id)
    edges = g.get_edge_data(prog_node_id, stmt_id)
    assert any(edges[idx]["relation"] == "EXECUTES" for idx in edges)

    # Verify SQLStatement --READS_TABLE--> MARA
    assert g.has_edge(stmt_id, "TABLE:ZTEST:MARA")
    edges_data = g.get_edge_data(stmt_id, "TABLE:ZTEST:MARA")
    assert any(edges_data[idx]["relation"] == "READS_TABLE" for idx in edges_data)
