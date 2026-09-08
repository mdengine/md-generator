from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class RelationshipType(str, Enum):
    CALLS = "CALLS"
    PERFORMS = "PERFORMS"
    INCLUDES = "INCLUDES"
    SUBMITS = "SUBMITS"
    CREATES = "CREATES"
    INSTANTIATES = "INSTANTIATES"
    USES = "USES"
    RAISES = "RAISES"
    CHECKS = "CHECKS"
    READS = "READS"
    WRITES = "WRITES"

class ResolutionStatus(str, Enum):
    STATIC = "STATIC"
    DYNAMIC = "DYNAMIC"
    UNRESOLVED = "UNRESOLVED"

@dataclass
class Node:
    id: str  # Stable ID, e.g., prog://ZREPORT, form://ZREPORT/INIT
    kind: str  # "EVENT", "FORM", "METHOD", "FUNCTION", "SUBMIT", "TRANSACTION", "SCREEN", "INCLUDE", "CREATE_OBJECT", "NEW", "STANDARD_SAP", "UNKNOWN"
    name: str
    display_name: str = ""
    qualified_name: str = ""
    namespace: str = ""
    program: str = ""
    package: str = ""
    include: str = ""
    line: int = 0
    line_start: int = 0
    line_end: int = 0
    source_file: str = ""
    is_standard: bool = False
    is_external: bool = False
    visibility: str = "local"  # "local", "global", "public"
    has_cycle: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name
        if not self.qualified_name:
            self.qualified_name = f"{self.program}/{self.name}" if self.program else self.name
        if not self.line_start:
            self.line_start = self.line

    @property
    def is_sap(self) -> bool:
        return self.is_standard

    @is_sap.setter
    def is_sap(self, value: bool) -> None:
        self.is_standard = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "display_name": self.display_name,
            "qualified_name": self.qualified_name,
            "namespace": self.namespace,
            "program": self.program,
            "package": self.package,
            "include": self.include,
            "line": self.line,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "source_file": self.source_file,
            "is_standard": self.is_standard,
            "is_sap": self.is_standard,  # Keep for backwards compatibility
            "is_external": self.is_external,
            "visibility": self.visibility,
            "has_cycle": self.has_cycle,
            "metadata": self.metadata,
        }

@dataclass
class Edge:
    source: str
    destination: str
    relationship: RelationshipType
    line_number: int = 0
    resolved: bool = True
    dynamic: bool = False
    confidence: float = 1.0
    resolution_status: ResolutionStatus = ResolutionStatus.STATIC

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "destination": self.destination,
            "relationship": self.relationship.value,
            "line_number": self.line_number,
            "resolved": self.resolved,
            "dynamic": self.dynamic,
            "confidence": self.confidence,
            "resolution_status": self.resolution_status.value,
        }

@dataclass
class CallGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def find_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def incoming(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.destination == node_id]

    def outgoing(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source == node_id]

    def successors(self, node_id: str) -> list[Node]:
        nodes_list = []
        for edge in self.outgoing(node_id):
            n = self.nodes.get(edge.destination)
            if n:
                nodes_list.append(n)
        return nodes_list

    def predecessors(self, node_id: str) -> list[Node]:
        nodes_list = []
        for edge in self.incoming(node_id):
            n = self.nodes.get(edge.source)
            if n:
                nodes_list.append(n)
        return nodes_list

    def roots(self) -> list[Node]:
        # Roots are nodes with no incoming edges
        destinations = {e.destination for e in self.edges}
        return [n for n in self.nodes.values() if n.id not in destinations]

    def leaf_nodes(self) -> list[Node]:
        # Leaf nodes are nodes with no outgoing edges
        sources = {e.source for e in self.edges}
        return [n for n in self.nodes.values() if n.id not in sources]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }

class GraphSerializer:
    @staticmethod
    def to_json(graph: CallGraph) -> str:
        return json.dumps(graph.to_dict(), indent=2)

    @staticmethod
    def from_json(json_str: str) -> CallGraph:
        data = json.loads(json_str)
        graph = CallGraph()
        for nid, nd in data.get("nodes", {}).items():
            # Handle backward compatibility / properties mapping
            is_standard = nd.get("is_standard", nd.get("is_sap", False))
            node_metadata = nd.get("metadata", {})
            graph.add_node(Node(
                id=nd["id"],
                kind=nd["kind"],
                name=nd["name"],
                display_name=nd.get("display_name", ""),
                qualified_name=nd.get("qualified_name", ""),
                namespace=nd.get("namespace", ""),
                program=nd.get("program", ""),
                package=nd.get("package", ""),
                include=nd.get("include", ""),
                line=nd.get("line", 0),
                line_start=nd.get("line_start", 0),
                line_end=nd.get("line_end", 0),
                source_file=nd.get("source_file", ""),
                is_standard=is_standard,
                is_external=nd.get("is_external", False),
                visibility=nd.get("visibility", "local"),
                has_cycle=nd.get("has_cycle", False),
                metadata=node_metadata
            ))
        for ed in data.get("edges", []):
            rel = RelationshipType(ed["relationship"])
            res_status = ResolutionStatus(ed.get("resolution_status", "STATIC"))
            graph.add_edge(Edge(
                source=ed["source"],
                destination=ed["destination"],
                relationship=rel,
                line_number=ed.get("line_number", 0),
                resolved=ed.get("resolved", True),
                dynamic=ed.get("dynamic", False),
                confidence=ed.get("confidence", 1.0),
                resolution_status=res_status
            ))
        return graph

    @staticmethod
    def to_yaml(graph: CallGraph) -> str:
        try:
            import yaml
            return yaml.dump(graph.to_dict(), sort_keys=False)
        except Exception:
            return str(graph.to_dict())

    @staticmethod
    def from_yaml(yaml_str: str) -> CallGraph:
        import yaml
        data = yaml.safe_load(yaml_str) or {}
        # Simple mapper reuse
        return GraphSerializer.from_json(json.dumps(data))

@dataclass
class CallReference:
    call_type: str  # e.g., "PERFORM", "PERFORM_IN_PROGRAM", "CALL_FUNCTION", "CALL_METHOD", ...
    target: str     # resolved or parsed name
    extra: str = "" # e.g. program name for PERFORM IN PROGRAM
    line: int = 0
    dynamic: bool = False

@dataclass
class AbapBlock:
    kind: str       # "EVENT" or "FORM" or "METHOD" or "FUNCTION"
    name: str       # e.g., "START-OF-SELECTION", "INIT_FORM"
    statements: list[tuple[int, str]] = field(default_factory=list)
    calls: list[CallReference] = field(default_factory=list)
