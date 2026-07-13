from __future__ import annotations

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

@dataclass
class Node:
    id: str  # Stable ID, e.g., prog://ZREPORT, form://ZREPORT/INIT
    kind: str  # "EVENT", "FORM", "METHOD", "FUNCTION", "SUBMIT", "TRANSACTION", "SCREEN", "INCLUDE", "CREATE_OBJECT", "NEW", "STANDARD_SAP", "UNKNOWN"
    name: str
    namespace: str = ""
    program: str = ""
    include: str = ""
    line: int = 0
    source_file: str = ""
    is_sap: bool = False
    is_external: bool = False
    visibility: str = "local"  # "local", "global", "public"
    has_cycle: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
            "program": self.program,
            "include": self.include,
            "line": self.line,
            "source_file": self.source_file,
            "is_sap": self.is_sap,
            "is_external": self.is_external,
            "visibility": self.visibility,
            "has_cycle": self.has_cycle,
        }

@dataclass
class Edge:
    source: str
    destination: str
    relationship: RelationshipType
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "destination": self.destination,
            "relationship": self.relationship.value,
            "line_number": self.line_number,
        }

@dataclass
class CallGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class CallReference:
    call_type: str  # e.g., "PERFORM", "PERFORM_IN_PROGRAM", "CALL_FUNCTION", "CALL_METHOD", "SUBMIT", "CALL_TRANSACTION", "CALL_SCREEN", "INCLUDE", "CREATE_OBJECT", "NEW"
    target: str     # resolved or parsed name
    extra: str = "" # e.g. program name for PERFORM IN PROGRAM
    line: int = 0


@dataclass
class AbapBlock:
    kind: str       # "EVENT" or "FORM" or "METHOD" or "FUNCTION"
    name: str       # e.g., "START-OF-SELECTION", "INIT_FORM"
    statements: list[tuple[int, str]] = field(default_factory=list)
    calls: list[CallReference] = field(default_factory=list)
