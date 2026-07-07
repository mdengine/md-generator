from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import networkx as nx

from md_generator.codeflow.enterprise_ir.runtime import RuntimeEvent


@dataclass
class RuntimeTrace:
    trace_id: str
    events: list[RuntimeEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeSession:
    session_id: str
    traces: list[RuntimeTrace] = field(default_factory=list)
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimeCorrelator:
    def __init__(self, static_graph: nx.MultiDiGraph) -> None:
        self.static_graph = static_graph

    def correlate(self, session: RuntimeSession) -> dict[str, Any]:
        """Correlates the static call tree/graph nodes with dynamic trace events."""
        correlation_map: dict[str, Any] = {}
        for trace in session.traces:
            for event in trace.events:
                # Basic matching heuristic: if event name matches or is part of a static node ID
                matched_nodes = []
                for node in self.static_graph.nodes:
                    if event.event_name in str(node):
                        matched_nodes.append(node)
                if matched_nodes:
                    correlation_map[event.event_name] = {
                        "static_nodes": matched_nodes,
                        "duration_ms": event.duration_ms,
                        "parameters": event.parameters,
                    }
        return correlation_map
