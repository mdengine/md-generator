"""Mermaid diagram exporter for journeys.

Renders JourneyIR and JourneyForest to Mermaid flowchart format (.mmd).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR, JourneyEdgeIR
from md_generator.codeflow.journey.tree import flatten_to_list


def _get_mermaid_id(node: JourneyNodeIR) -> str:
    """Generate a safe, unique Mermaid identifier for a node based on its branch ID."""
    return "n_" + node.branch_id.replace(".", "_")


def _escape_label(label: str) -> str:
    """Escape quotes and other special characters for Mermaid labels."""
    return label.replace('"', '\\"')


def _get_node_shape(node: JourneyNodeIR, mermaid_id: str) -> str:
    """Return the Mermaid node definition with the correct shape based on type."""
    lbl = _escape_label(node.label)
    nt_lower = (node.node_type or "").lower()

    if nt_lower in ("table", "collection", "database"):
        if not lbl.upper().startswith("TABLE:"):
            return f'{mermaid_id}[("TABLE: {lbl}")]'
        return f'{mermaid_id}[("{lbl}")]'
    elif nt_lower in ("topic", "queue"):
        return f'{mermaid_id}(["{lbl}"])'
    elif nt_lower in ("config", "configuration"):
        return f'{mermaid_id}[/"{lbl}"/]'
    elif nt_lower in ("external", "external_api"):
        return f'{mermaid_id}{{"{lbl}"}}'
    elif nt_lower == "file":
        return f'{mermaid_id}("{lbl}")'
    else:
        return f'{mermaid_id}["{lbl}"]'


def journey_to_mermaid(ir: JourneyIR) -> str:
    """Render JourneyIR to a top-down Mermaid graph flow string."""
    all_nodes = flatten_to_list(ir.root)
    if not all_nodes:
        return "graph TD\n    empty[Empty Journey]\n"

    lines = ["graph TD"]
    
    # 1. Define nodes and group them by language subgraphs
    nodes_by_language: dict[str, list[JourneyNodeIR]] = defaultdict(list)
    unknown_lang_nodes: list[JourneyNodeIR] = []
    
    for node in all_nodes:
        if node.language:
            nodes_by_language[node.language.lower()].append(node)
        else:
            unknown_lang_nodes.append(node)

    # Styling colors for subgraphs
    lang_colors = {
        "java": ("#f4f8ff", "#2b579a"),
        "python": ("#fffbf0", "#306998"),
        "javascript": ("#f9f0ff", "#8a2be2"),
        "typescript": ("#f9f0ff", "#007acc"),
        "tsx": ("#f9f0ff", "#007acc"),
        "go": ("#e6fcff", "#00add8"),
        "c": ("#fff5f5", "#a82b2b"),
        "c++": ("#fff5f5", "#a82b2b"),
        "cpp": ("#fff5f5", "#a82b2b"),
        "csharp": ("#fbf4ff", "#178600"),
        "kotlin": ("#f9f5ff", "#f18e33"),
        "swift": ("#fff6f0", "#ffac45"),
        "ruby": ("#fff0f2", "#701516"),
        "rust": ("#fff2e8", "#dea584"),
        "php": ("#f0f1fa", "#4f5b93"),
    }

    # Output subgraphs
    for lang, lnodes in sorted(nodes_by_language.items()):
        lang_cap = lang.capitalize()
        lines.append(f"    subgraph Lang_{lang_cap} [\"{lang_cap} Components\"]")
        bg_col, border_col = lang_colors.get(lang, ("#f5f5f5", "#7f7f7f"))
        lines.append(f"        style Lang_{lang_cap} fill:{bg_col},stroke:{border_col},stroke-width:1px")
        for node in lnodes:
            m_id = _get_mermaid_id(node)
            lines.append(f"        {_get_node_shape(node, m_id)}")
        lines.append("    end")
        lines.append("")

    # Define unknown language nodes
    if unknown_lang_nodes:
        for node in unknown_lang_nodes:
            m_id = _get_mermaid_id(node)
            lines.append(f"    {_get_node_shape(node, m_id)}")

    # 2. Connect nodes with edges
    # We walk the tree and connect parents to children
    edge_styles: list[str] = []
    link_counter = 0

    def _connect_edges(node: JourneyNodeIR) -> None:
        nonlocal link_counter
        p_id = _get_mermaid_id(node)
        for child in node.children:
            c_id = _get_mermaid_id(child)
            
            # Formatting the edge label
            edge_relation = child.edge_relation or "CALLS"
            is_async = child.call_type == "async"
            edge_lbl_parts = [edge_relation]
            
            if is_async:
                edge_lbl_parts.append("async")
            if child.edge_label:
                edge_lbl_parts.append(f"if {child.edge_label}")
            if child.is_cycle:
                edge_lbl_parts.append("cycle")
                
            edge_lbl = " | ".join(edge_lbl_parts)
            
            # Select arrow style
            if is_async or child.is_cycle:
                arrow = f"-.->|\"{_escape_label(edge_lbl)}\"|"
            else:
                arrow = f"-->|\"{_escape_label(edge_lbl)}\"|"
                
            lines.append(f"    {p_id} {arrow} {c_id}")
            
            # Dotted red style for cycle edges
            if child.is_cycle:
                edge_styles.append(f"    linkStyle {link_counter} stroke:#ff3333,stroke-width:2px,stroke-dasharray:5 5")
                
            link_counter += 1
            _connect_edges(child)

    _connect_edges(ir.root)
    lines.append("")
    lines.extend(edge_styles)

    return "\n".join(lines) + "\n"


def write_journey_mermaid(ir: JourneyIR, path: Path) -> None:
    """Write journey Mermaid diagram to a file."""
    content = journey_to_mermaid(ir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
