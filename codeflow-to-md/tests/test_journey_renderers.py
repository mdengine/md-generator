from __future__ import annotations

from pathlib import Path
from md_generator.codeflow.journey import JourneyNodeIR, JourneyIR, JourneyStatistics, JourneyEdgeIR
from md_generator.codeflow.journey.markdown import write_journey_markdown, write_repository_journey_summary
from md_generator.codeflow.journey.mermaid import write_journey_mermaid
from md_generator.codeflow.journey.html import write_journey_html
from md_generator.codeflow.journey.json_export import write_journey_json
from md_generator.codeflow.journey.graph_export import write_journey_dot, write_journey_graphml, write_journey_gexf


def test_exporters(tmp_path: Path) -> None:
    # Build tree
    root = JourneyNodeIR(id="root", label="root()", node_type="method", depth=0)
    c1 = JourneyNodeIR(id="c1", label="c1()", node_type="method", depth=1, edge_relation="CALLS")
    root.children = [c1]
    root.is_leaf = False
    
    ir = JourneyIR(
        root=root,
        statistics=JourneyStatistics(node_count=2, maximum_depth=1),
        edges=[JourneyEdgeIR("root", "c1", "CALLS")]
    )
    
    # 1. Markdown Exporter
    md_path = tmp_path / "journey.md"
    write_journey_markdown(ir, md_path)
    assert md_path.exists()
    
    # 2. Summary Exporter
    sum_path = tmp_path / "summary.md"
    write_repository_journey_summary([ir], sum_path)
    assert sum_path.exists()
    
    # 3. Mermaid Exporter
    mmd_path = tmp_path / "journey.mmd"
    write_journey_mermaid(ir, mmd_path)
    assert mmd_path.exists()
    
    # 4. JSON Exporter
    json_path = tmp_path / "journey.json"
    write_journey_json(ir, json_path)
    assert json_path.exists()
    
    # 5. Graph Exporters (DOT, GraphML, GEXF)
    dot_path = tmp_path / "journey.dot"
    write_journey_dot(ir, dot_path)
    assert dot_path.exists()
    
    gml_path = tmp_path / "journey.graphml"
    write_journey_graphml(ir, gml_path)
    assert gml_path.exists()
    
    gexf_path = tmp_path / "journey.gexf"
    write_journey_gexf(ir, gexf_path)
    assert gexf_path.exists()
    
    # 6. HTML Exporter
    html_path = tmp_path / "journey.html"
    write_journey_html(ir, html_path)
    assert html_path.exists()
