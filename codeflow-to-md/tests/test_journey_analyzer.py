from __future__ import annotations

from pathlib import Path
import networkx as nx
from md_generator.codeflow.graph.multigraph_utils import CodeflowGraph
from md_generator.codeflow.journey import JourneyNodeIR, JourneyIR, JourneyStatistics
from md_generator.codeflow.journey.analyzer import JourneyAnalyzer, write_journey_analysis_markdown
from md_generator.codeflow.journey.paths import enumerate_execution_paths


def test_journey_analyzer(tmp_path: Path) -> None:
    g = nx.MultiDiGraph()
    g.add_node("root", type="method", label="root")
    g.add_node("c1", type="method", label="c1")
    g.add_node("c2", type="method", label="c2")
    g.add_node("unused", type="method", label="unused")
    
    g.add_edge("root", "c1", relation="CALLS")
    g.add_edge("root", "c2", relation="CALLS")
    
    # Build tree
    root = JourneyNodeIR(id="root", label="root()", node_type="method", depth=0)
    c1 = JourneyNodeIR(id="c1", label="c1()", node_type="method", depth=1, edge_relation="CALLS")
    c2 = JourneyNodeIR(id="c2", label="c2()", node_type="method", depth=1, edge_relation="CALLS")
    root.children = [c1, c2]
    root.is_leaf = False
    
    ir = JourneyIR(root=root, statistics=JourneyStatistics(node_count=3, maximum_depth=1))
    ir.execution_paths = enumerate_execution_paths(ir)
    
    analyzer = JourneyAnalyzer(ir, g)
    analysis = analyzer.analyze()
    
    assert analysis.longest_journey is not None
    assert analysis.longest_journey.depth == 2
    assert analysis.deepest_call.id in ("c1", "c2")
    assert "unused" in analysis.unused_journeys
    assert "c1" not in analysis.unused_journeys
    
    # Write analysis
    md_out = tmp_path / "analysis.md"
    write_journey_analysis_markdown(analysis, md_out)
    assert md_out.exists()
