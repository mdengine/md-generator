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
