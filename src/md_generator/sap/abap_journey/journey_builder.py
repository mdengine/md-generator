from __future__ import annotations

from dataclasses import dataclass
from md_generator.sap.abap_journey.models import CallGraph, Node

@dataclass
class ExecutionPhase:
    phase_name: str
    root_nodes: list[Node]
    graph: CallGraph

class JourneyBuilder:
    @staticmethod
    def build_phases(graph: CallGraph) -> list[ExecutionPhase]:
        phases: list[ExecutionPhase] = []

        # Find all event nodes
        event_nodes = [n for n in graph.nodes.values() if n.kind == "EVENT"]

        if not event_nodes:
            # Fallback if no EVENT blocks exist:
            # Find all nodes of kind METHOD, FORM, FUNCTION, BEHAVIOR, or AMDP that act as entry points
            # (i.e. roots, or whose only incoming edge is from a PROGRAM node)
            entry_nodes: list[Node] = []
            for node in graph.nodes.values():
                if node.kind in ("METHOD", "FORM", "FUNCTION", "BEHAVIOR", "AMDP"):
                    incoming_edges = graph.incoming(node.id)
                    is_entry = False
                    if not incoming_edges:
                        is_entry = True
                    else:
                        # If the only incoming edge is from the root PROGRAM node
                        is_only_prog = all(
                            graph.nodes.get(e.source) and graph.nodes[e.source].kind == "PROGRAM"
                            for e in incoming_edges
                        )
                        if is_only_prog:
                            is_entry = True
                    if is_entry:
                        entry_nodes.append(node)

            if entry_nodes:
                phases.append(ExecutionPhase(
                    phase_name="Entry Points (Methods / Subroutines / Functions)",
                    root_nodes=entry_nodes,
                    graph=graph
                ))
            return phases

        # Priority sort
        event_priority = [
            "LOAD-OF-PROGRAM",
            "INITIALIZATION",
            "AT SELECTION-SCREEN",
            "START-OF-SELECTION",
            "END-OF-SELECTION",
            "TOP-OF-PAGE",
            "END-OF-PAGE"
        ]

        def priority(name: str) -> int:
            name_upper = name.upper()
            for i, kw in enumerate(event_priority):
                if name_upper.startswith(kw):
                    return i
            return len(event_priority)

        sorted_events = sorted(event_nodes, key=lambda n: (priority(n.name), n.name))

        for event in sorted_events:
            # Find directly outgoing calls from this event
            out_edges = [e for e in graph.edges if e.source == event.id]
            dest_nodes: list[Node] = []
            for edge in out_edges:
                dest = graph.nodes.get(edge.destination)
                if dest:
                    dest_nodes.append(dest)
            phases.append(ExecutionPhase(phase_name=event.name, root_nodes=dest_nodes, graph=graph))

        return phases
