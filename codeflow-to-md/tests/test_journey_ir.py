from __future__ import annotations

from md_generator.codeflow.journey import (
    CfgOverlay,
    JourneyEdgeIR,
    JourneyNodeIR,
    JourneyMetadata,
    JourneyIR,
    JourneyStatistics,
)


def test_cfg_overlay() -> None:
    c = CfgOverlay(kind="IF", condition="x > 5")
    assert c.kind == "IF"
    assert c.condition == "x > 5"
    assert c.label is None
    assert c.children == []


def test_journey_edge_ir() -> None:
    e = JourneyEdgeIR(source_id="n1", target_id="n2", relation="CALLS")
    assert e.source_id == "n1"
    assert e.target_id == "n2"
    assert e.relation == "CALLS"
    assert e.label is None
    assert e.confidence == 1.0
    assert e.is_async is False
    assert e.is_cycle_edge is False
    assert e.annotations == {}


def test_journey_node_ir() -> None:
    n = JourneyNodeIR(id="main", label="main()", node_type="method")
    assert n.id == "main"
    assert n.label == "main()"
    assert n.node_type == "method"
    assert n.language is None
    assert n.depth == 0
    assert n.branch_id == "0"
    assert n.is_leaf is True
    assert n.is_root is False
    assert n.children == []


def test_journey_metadata() -> None:
    m = JourneyMetadata(entry_id="start", entry_label="start()")
    assert m.entry_id == "start"
    assert m.entry_label == "start()"
    assert m.schema_version == "1.0"
    assert m.total_nodes == 0
    assert m.total_depth == 0
    assert m.truncated is False
    assert m.cycle_nodes == set()


def test_journey_ir() -> None:
    root = JourneyNodeIR(id="root", label="root()", node_type="method")
    ir = JourneyIR(root=root)
    assert ir.root == root
    assert isinstance(ir.metadata, JourneyMetadata)
    assert isinstance(ir.statistics, JourneyStatistics)
    assert ir.edges == []
    assert ir.execution_paths is None
