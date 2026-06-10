from __future__ import annotations

from collections import deque
from typing import Iterable

from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType


class InMemoryGraphStore:
    def __init__(self, graph_id: str = "run") -> None:
        self._graph = ArtifactGraph(graph_id=graph_id)

    @property
    def graph(self) -> ArtifactGraph:
        return self._graph

    def add_fragment(self, fragment: ArtifactGraph) -> None:
        self._graph.merge(fragment)

    def add_node(self, node: GraphNode) -> None:
        self._graph.add_node(node)

    def add_edge(self, edge: GraphEdge) -> None:
        self._graph.add_edge(edge)

    def upstream(
        self,
        node_id: str,
        *,
        relationship_types: Iterable[RelationshipType] | None = None,
        max_depth: int = 50,
    ) -> set[str]:
        allowed = set(relationship_types) if relationship_types else None
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(node_id, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in self._graph.edges.values():
                if edge.target_id != current:
                    continue
                if allowed and edge.relationship not in allowed:
                    continue
                if edge.source_id not in visited:
                    visited.add(edge.source_id)
                    queue.append((edge.source_id, depth + 1))
        return visited

    def downstream(
        self,
        node_id: str,
        *,
        relationship_types: Iterable[RelationshipType] | None = None,
        max_depth: int = 50,
    ) -> set[str]:
        allowed = set(relationship_types) if relationship_types else None
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(node_id, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in self._graph.edges.values():
                if edge.source_id != current:
                    continue
                if allowed and edge.relationship not in allowed:
                    continue
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, depth + 1))
        return visited

    def column_lineage(self, column_node_id: str) -> list[GraphEdge]:
        return [
            e
            for e in self._graph.edges.values()
            if e.relationship in (RelationshipType.DERIVES_FROM, RelationshipType.TRANSFORMS)
            and (e.target_id == column_node_id or e.source_id == column_node_id)
        ]

    def to_dict(self) -> dict:
        return self._graph.model_dump(mode="json")


# Backward-compatible alias
ArtifactGraphStore = InMemoryGraphStore
