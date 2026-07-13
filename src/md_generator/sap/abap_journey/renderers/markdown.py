from __future__ import annotations

from md_generator.sap.abap_journey.models import CallGraph, Node
from md_generator.sap.abap_journey.journey_builder import ExecutionPhase

class MarkdownRenderer:
    @staticmethod
    def format_text_tree(nodes: list[Node], graph: CallGraph) -> str:
        lines: list[str] = []
        global_visited = set()

        def _render(node: Node, prefix: str = "", is_last: bool = True, path_visited: set[str] = None):
            if path_visited is None:
                path_visited = set()
                
            connector = "└── " if is_last else "├── "
            extra = ""
            if node.is_sap:
                extra = " (SAP Standard)"
            elif node.has_cycle or node.id in path_visited:
                extra = " (Recursive Cycle 🔄)"

            line_info = f" @ line {node.line}" if node.line > 0 else ""
            lines.append(f"{prefix}{connector}{node.kind}: {node.name}{extra}{line_info}")

            # Cycle check for rendering child elements
            if node.id in path_visited or node.has_cycle:
                return

            path_visited.add(node.id)

            # Find all outgoing edges from this node
            out_edges = [e for e in graph.edges if e.source == node.id]
            children = []
            for edge in out_edges:
                child = graph.nodes.get(edge.destination)
                if child:
                    children.append(child)

            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(children):
                _render(child, new_prefix, i == len(children) - 1, path_visited.copy())

        for i, node in enumerate(nodes):
            _render(node, is_last=(i == len(nodes) - 1))

        return "\n".join(lines)

    @staticmethod
    def render(
        program_name: str,
        graph: CallGraph,
        phases: list[ExecutionPhase]
    ) -> str:
        # Collect statistics and dependencies from nodes
        total_forms = set()
        total_methods = set()
        total_functions = set()
        total_includes = set()
        sap_standard_calls = set()
        external_dependencies = set()
        has_cycle = False

        for node in graph.nodes.values():
            if node.has_cycle:
                has_cycle = True
            if node.is_sap:
                sap_standard_calls.add(node.name.upper())

            ukey = node.name.upper()
            if node.kind == "FORM" or node.kind == "PERFORM_IN_PROGRAM":
                total_forms.add(ukey)
                if node.is_external:
                    external_dependencies.add(f"Subroutine: {ukey} in Program {node.program.upper()}")
            elif node.kind == "CALL_FUNCTION":
                total_functions.add(ukey)
                if not node.is_sap:
                    external_dependencies.add(f"Function Module: {ukey}")
            elif node.kind == "CALL_METHOD":
                total_methods.add(ukey)
                if not node.is_sap:
                    external_dependencies.add(f"Method: {ukey}")
            elif node.kind == "INCLUDE":
                total_includes.add(ukey)

        # Build Markdown sections
        sections: list[str] = []

        # 1. Execution Journey Section
        sections.append("## ABAP Execution Journey\n")
        if not phases or all(not p.root_nodes for p in phases):
            sections.append("_No explicit execution phases or subroutine calls detected._\n")
        else:
            for phase in phases:
                if not phase.root_nodes:
                    continue
                sections.append(f"### Phase: {phase.phase_name}")
                tree_str = MarkdownRenderer.format_text_tree(phase.root_nodes, graph)
                sections.append(f"```text\n{tree_str}\n```\n")

        # 2. Call Graph Visualizations
        sections.append("## Call Graph Visualization\n")
        # Check if we have valid non-event calls
        has_calls = any(n.kind != "EVENT" and n.kind != "PROGRAM" for n in graph.nodes.values())
        if has_calls:
            from md_generator.sap.abap_journey.renderers.mermaid import MermaidRenderer
            mermaid_flow = MermaidRenderer.render(graph)
            sections.append("```mermaid\n" + mermaid_flow + "\n```\n")
        else:
            sections.append("_No call graph to visualize._\n")

        # 3. External Dependencies
        sections.append("## External Dependencies\n")
        if external_dependencies:
            for dep in sorted(external_dependencies):
                sections.append(f"- {dep}")
        else:
            sections.append("_No external custom dependencies detected._")
        sections.append("")

        # 4. SAP Standard Calls
        sections.append("## SAP Standard Calls\n")
        if sap_standard_calls:
            for call in sorted(sap_standard_calls):
                sections.append(f"- `{call}` (SAP Standard)")
        else:
            sections.append("_No standard SAP calls detected._")
        sections.append("")

        # 5. Statistics
        sections.append("## Static Analysis Statistics\n")
        sections.append(f"- **Total Subroutines (FORMs):** {len(total_forms)}")
        sections.append(f"- **Total Methods Called:** {len(total_methods)}")
        sections.append(f"- **Total Function Modules Called:** {len(total_functions)}")
        sections.append(f"- **Total Includes Expanded:** {len(total_includes)}")
        sections.append(f"- **Detected Cycles/Recursion:** {'Yes 🔄' if has_cycle else 'No'}")
        sections.append("")

        return "\n".join(sections)
