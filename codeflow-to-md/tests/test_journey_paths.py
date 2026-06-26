from __future__ import annotations

from pathlib import Path
from md_generator.codeflow.journey import JourneyNodeIR, JourneyIR
from md_generator.codeflow.journey.paths import (
    enumerate_execution_paths,
    write_execution_paths_markdown,
)
from md_generator.codeflow.journey.json_export import write_generic_json


def test_path_enumeration(tmp_path: Path) -> None:
    # Build tree
    # root -> child1 (method)
    #      -> child2 (database)
    root = JourneyNodeIR(id="root", label="root()", node_type="method", depth=0)
    c1 = JourneyNodeIR(id="c1", label="c1()", node_type="method", depth=1, edge_relation="CALLS")
    c2 = JourneyNodeIR(id="c2", label="c2_db", node_type="table", depth=1, edge_relation="READS")
    root.children = [c1, c2]
    root.is_leaf = False
    
    ir = JourneyIR(root=root)
    
    paths = enumerate_execution_paths(ir)
    assert len(paths) == 2
    
    # Check Path 1
    p1 = paths[0]
    assert p1.nodes == ["root", "c1"]
    assert p1.labels == ["root()", "c1()"]
    assert p1.has_database is False
    assert p1.terminal_node_type == "method"
    
    # Check Path 2
    p2 = paths[1]
    assert p2.nodes == ["root", "c2"]
    assert p2.labels == ["root()", "c2_db"]
    assert p2.has_database is True
    assert p2.terminal_node_type == "table"
    
    # Write to files
    md_out = tmp_path / "paths.md"
    write_execution_paths_markdown(paths, md_out)
    assert md_out.exists()
    
    json_out = tmp_path / "paths.json"
    write_generic_json(paths, json_out)
    assert json_out.exists()
