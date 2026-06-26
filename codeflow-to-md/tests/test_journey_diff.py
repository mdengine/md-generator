from __future__ import annotations

from pathlib import Path
from md_generator.codeflow.journey import JourneyNodeIR, JourneyIR, JourneyEdgeIR, JourneyStatistics
from md_generator.codeflow.journey.diff import compute_journey_diff, write_journey_diff_markdown
from md_generator.codeflow.journey.paths import enumerate_execution_paths


def test_journey_diff_calculation(tmp_path: Path) -> None:
    # 1. Base Journey: root -> c1
    root_b = JourneyNodeIR(id="root", label="root()", node_type="method", depth=0)
    c1_b = JourneyNodeIR(id="c1", label="c1()", node_type="method", depth=1, edge_relation="CALLS")
    root_b.children = [c1_b]
    root_b.is_leaf = False
    ir_base = JourneyIR(
        root=root_b,
        statistics=JourneyStatistics(node_count=2, maximum_depth=1),
        edges=[JourneyEdgeIR("root", "c1", "CALLS")]
    )
    ir_base.execution_paths = enumerate_execution_paths(ir_base)
    
    # 2. Head Journey: root -> c1 -> c2 (new node)
    root_h = JourneyNodeIR(id="root", label="root()", node_type="method", depth=0)
    c1_h = JourneyNodeIR(id="c1", label="c1()", node_type="method", depth=1, edge_relation="CALLS")
    c2_h = JourneyNodeIR(id="c2", label="c2()", node_type="method", depth=2, edge_relation="CALLS")
    root_h.children = [c1_h]
    c1_h.children = [c2_h]
    c1_h.is_leaf = False
    root_h.is_leaf = False
    
    ir_head = JourneyIR(
        root=root_h,
        statistics=JourneyStatistics(node_count=3, maximum_depth=2),
        edges=[
            JourneyEdgeIR("root", "c1", "CALLS"),
            JourneyEdgeIR("c1", "c2", "CALLS"),
        ]
    )
    ir_head.execution_paths = enumerate_execution_paths(ir_head)
    
    # Compute Diff
    diff = compute_journey_diff(ir_base, ir_head, "commit_base", "commit_head")
    
    assert diff.base_commit == "commit_base"
    assert diff.head_commit == "commit_head"
    assert len(diff.added_nodes) == 1
    assert diff.added_nodes[0]["id"] == "c2"
    assert len(diff.added_edges) == 1
    assert diff.added_edges[0]["source_id"] == "c1"
    assert diff.added_edges[0]["target_id"] == "c2"
    assert diff.node_count_change == 1
    assert diff.depth_change == 1
    
    # Write Diff Markdown
    md_out = tmp_path / "diff.md"
    write_journey_diff_markdown(diff, md_out)
    assert md_out.exists()
