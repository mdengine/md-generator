from __future__ import annotations

"""GraphStore Protocol Definition for md-generator Knowledge Graph Layer."""

from typing import List, Optional, Tuple, Set, Literal, Protocol, runtime_checkable
from md_generator.graph.model import EntityNode, RelationEdge, KnowledgeGraph


@runtime_checkable
class GraphStore(Protocol):
    """Protocol defining multi-tenant graph storage, traversal, and lifecycle contracts."""

    def initialize(self) -> None:
        """Initializes the graph store connection, indices, and constraints."""
        ...

    def health_check(self) -> bool:
        """Executes a lightweight connectivity/liveness health check."""
        ...

    def upsert_nodes(self, nodes: List[EntityNode], tenant_id: str) -> int:
        """Upserts a list of entity nodes within the specified tenant boundary."""
        ...

    def upsert_edges(self, edges: List[RelationEdge], tenant_id: str) -> int:
        """Upserts a list of relationship edges within the specified tenant boundary."""
        ...

    def upsert_graph(self, graph: KnowledgeGraph, tenant_id: str) -> Tuple[int, int]:
        """Upserts a complete KnowledgeGraph within the specified tenant boundary.
        
        Returns:
            Tuple[int, int]: Count of upserted nodes and edges.
        """
        ...

    def get_node(self, node_id: str, tenant_id: str) -> Optional[EntityNode]:
        """Retrieves an entity node by ID scoped strictly to tenant_id."""
        ...

    def get_neighbors(
        self,
        node_id: str,
        tenant_id: str,
        direction: Literal["in", "out", "both"] = "both",
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 1,
        max_nodes: int = 500,
        max_edges: int = 2000,
        strict_limits: bool = False,
    ) -> List[Tuple[RelationEdge, EntityNode]]:
        """Retrieves adjacent neighbors for a given node within tenant boundary.
        
        Enforces resource safety caps (max_nodes, max_edges).
        """
        ...

    def traverse(
        self,
        start_node_ids: List[str],
        tenant_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[str]] = None,
        direction: Literal["in", "out", "both"] = "both",
        strategy: Literal["bfs", "dfs"] = "bfs",
        max_nodes: int = 500,
        max_edges: int = 2000,
        strict_limits: bool = False,
    ) -> KnowledgeGraph:
        """Performs a multi-hop graph traversal starting from start_node_ids.
        
        Enforces tenant isolation, cycle detection, and resource safety limits.
        """
        ...

    def delete_by_tenant(self, tenant_id: str) -> int:
        """Deletes all graph nodes and edges belonging strictly to the specified tenant."""
        ...

    def delete_by_document(self, document_id: str, tenant_id: str) -> int:
        """Reconciles and purges graph entities and edges associated with document_id."""
        ...

    def contains_nodes(self, node_ids: List[str], tenant_id: str) -> Set[str]:
        """Returns the subset of node_ids that currently exist within tenant boundary."""
        ...

    def close(self) -> None:
        """Closes connections, pools, and releases store resources."""
        ...
