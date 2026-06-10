from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from md_generator.sap.graph.taxonomy import RelationshipType


class GraphNode(BaseModel):
    node_id: str
    node_kind: str = "artifact"
    label: str = ""
    namespace: str = ""
    artifact_type: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    edge_id: str
    source_id: str
    target_id: str
    relationship: RelationshipType
    properties: dict[str, Any] = Field(default_factory=dict)


class ArtifactGraph(BaseModel):
    graph_id: str = "default"
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: dict[str, GraphEdge] = Field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges[edge.edge_id] = edge

    def merge(self, other: ArtifactGraph) -> None:
        for node in other.nodes.values():
            if node.node_id in self.nodes:
                existing = self.nodes[node.node_id]
                merged_props = {**existing.properties, **node.properties}
                self.nodes[node.node_id] = node.model_copy(update={"properties": merged_props})
            else:
                self.nodes[node.node_id] = node
        for edge in other.edges.values():
            self.edges[edge.edge_id] = edge
