"""Graph format exporter for journeys.

Converts JourneyIR to NetworkX DiGraph and exports to DOT, GraphML, and GEXF formats.
"""

from __future__ import annotations

from pathlib import Path
import networkx as nx

from md_generator.codeflow.journey.ir import JourneyIR
from md_generator.codeflow.journey.tree import flatten_to_list


def _build_networkx_graph(ir: JourneyIR) -> nx.DiGraph:
    """Build a temporary NetworkX DiGraph from JourneyIR for graph export format conversion."""
    dg = nx.DiGraph()
    all_nodes = flatten_to_list(ir.root)
    
    for n in all_nodes:
        if n.id not in dg:
            # Use safe XML-compatible primitives for attributes
            attrs = {
                "label": n.label,
                "node_type": n.node_type,
                "language": n.language or "",
                "file_path": n.file_path or "",
                "class_name": n.class_name or "",
                "method_name": n.method_name or "",
                "framework": n.framework or "",
                "line": n.line if n.line is not None else -1,
                "depth": n.depth,
                "is_cycle": int(n.is_cycle),
                "is_recursive": int(n.is_recursive),
                "stop_reason": n.stop_reason.value if n.stop_reason else "",
            }
            dg.add_node(n.id, **attrs)
            
    for e in ir.edges:
        edge_attrs = {
            "relation": e.relation,
            "label": e.label or "",
            "call_type": e.call_type or "",
            "confidence": e.confidence,
            "is_async": int(e.is_async),
            "is_cycle_edge": int(e.is_cycle_edge),
        }
        dg.add_edge(e.source_id, e.target_id, **edge_attrs)
        
    return dg


def write_journey_dot(ir: JourneyIR, path: Path) -> None:
    """Write journey in Graphviz DOT format."""
    dg = _build_networkx_graph(ir)
    lines = ["digraph Journey {"]
    # Node styling
    for n, d in dg.nodes(data=True):
        label = d.get("label", str(n)).replace('"', '\\"')
        lines.append(f'  "{n}" [label="{label}", type="{d.get("node_type")}", lang="{d.get("language")}"];')
    # Edge styling
    for u, v, d in dg.edges(data=True):
        rel = d.get("relation", "CALLS")
        lbl = d.get("label", "")
        if lbl:
            lbl_str = f' [label="{lbl}"]'
        else:
            lbl_str = ""
        lines.append(f'  "{u}" -> "{v}"{lbl_str};')
    lines.append("}")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_journey_graphml(ir: JourneyIR, path: Path) -> None:
    """Write journey in GraphML format."""
    dg = _build_networkx_graph(ir)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(dg, str(path))


def write_journey_gexf(ir: JourneyIR, path: Path) -> None:
    """Write journey in GEXF format."""
    dg = _build_networkx_graph(ir)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(dg, str(path))
