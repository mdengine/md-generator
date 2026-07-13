from __future__ import annotations

from md_generator.sap.abap_journey.models import CallGraph

class GraphvizRenderer:
    @staticmethod
    def render(graph: CallGraph) -> str:
        lines: list[str] = [
            "digraph G {",
            '    node [shape=box, fontname="Courier"];'
        ]
        node_ids: dict[str, str] = {}
        counter = 0

        def get_id(node_id: str) -> str:
            nonlocal counter
            if node_id not in node_ids:
                node_ids[node_id] = f"n{counter}"
                counter += 1
            return node_ids[node_id]

        for node in graph.nodes.values():
            nid = get_id(node.id)
            extra = ""
            if node.is_sap:
                extra = " (SAP Standard)"
            elif node.has_cycle:
                extra = " (Recursive)"
            label = f"{node.kind}: {node.name}{extra}"
            lines.append(f'    {nid} [label="{label}"];')

        for edge in graph.edges:
            src = get_id(edge.source)
            dst = get_id(edge.destination)
            lines.append(f'    {src} -> {dst} [label="{edge.relationship.value}"];')

        lines.append("}")
        return "\n".join(lines)
