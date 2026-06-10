from __future__ import annotations

from typing import Iterable, Protocol

from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType


class GraphStore(Protocol):
    @property
    def graph(self) -> ArtifactGraph: ...

    def add_fragment(self, fragment: ArtifactGraph) -> None: ...

    def add_node(self, node: GraphNode) -> None: ...

    def add_edge(self, edge: GraphEdge) -> None: ...

    def upstream(
        self,
        node_id: str,
        *,
        relationship_types: Iterable[RelationshipType] | None = None,
        max_depth: int = 50,
    ) -> set[str]: ...

    def downstream(
        self,
        node_id: str,
        *,
        relationship_types: Iterable[RelationshipType] | None = None,
        max_depth: int = 50,
    ) -> set[str]: ...

    def column_lineage(self, column_node_id: str) -> list[GraphEdge]: ...

    def to_dict(self) -> dict: ...
