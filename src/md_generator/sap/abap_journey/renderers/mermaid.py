from __future__ import annotations

from md_generator.sap.abap_journey.models import CallGraph

class MermaidRenderer:
    @staticmethod
    def render(graph: CallGraph) -> str:
        lines: list[str] = ["graph TD"]
        node_ids: dict[str, str] = {}
        counter = 0

        def get_id(node_id: str) -> str:
            nonlocal counter
            if node_id not in node_ids:
                node_ids[node_id] = f"n{counter}"
                counter += 1
            return node_ids[node_id]

        for node in graph.nodes.values():
            node_id = get_id(node.id)
            extra = ""
            if node.is_sap:
                extra = "\\n(SAP Standard)"
            elif node.has_cycle:
                extra = "\\n(Recursive Cycle)"
            lines.append(f'    {node_id}["{node.kind}: {node.name}{extra}"]')

        for edge in graph.edges:
            src_id = get_id(edge.source)
            dst_id = get_id(edge.destination)
            lines.append(f"    {src_id} -->|{edge.relationship.value}| {dst_id}")

        return "\n".join(lines)
