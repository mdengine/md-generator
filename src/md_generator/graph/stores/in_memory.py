from __future__ import annotations

"""Pure Standard Library InMemoryGraphStore implementation.

Phase 2C Implementation: In-memory graph storage, multi-tenant partitioning,
BFS/DFS traversal with cycle detection, deterministic neighbor ordering,
resource safety limits, and 5-step document lifecycle reconciliation.
"""

from collections import defaultdict, deque
import copy
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from md_generator.graph.exceptions import GraphQueryError, TenantBoundaryError
from md_generator.graph.model import (
    EntityNode,
    KnowledgeGraph,
    RelationEdge,
    _validate_tenant_id,
    canonical_document_node_id,
)
from md_generator.graph.protocol import GraphStore


class InMemoryGraphStore(GraphStore):
    """Pure standard-library multi-tenant graph store."""

    def __init__(self) -> None:
        # tenant_id -> node_id -> EntityNode
        self._nodes: Dict[str, Dict[str, EntityNode]] = defaultdict(dict)
        # tenant_id -> edge_id -> RelationEdge
        self._edges: Dict[str, Dict[str, RelationEdge]] = defaultdict(dict)
        # tenant_id -> source_node_id -> list of edge_ids
        self._out_edges: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        # tenant_id -> target_node_id -> list of edge_ids
        self._in_edges: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self._initialized: bool = False

    def initialize(self) -> None:
        """Initializes the graph store."""
        self._initialized = True

    def health_check(self) -> bool:
        """Returns True if the store is initialized and operational."""
        return True

    def close(self) -> None:
        """Closes store resources."""
        self._initialized = False

    def upsert_nodes(self, nodes: List[EntityNode], tenant_id: str) -> int:
        """Upserts a list of entity nodes within the specified tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.upsert_nodes.tenant_id")
        count = 0
        for node in nodes:
            if node.tenant_id != clean_tenant:
                raise TenantBoundaryError(
                    f"EntityNode '{node.node_id}' tenant_id '{node.tenant_id}' conflicts with operation tenant_id '{clean_tenant}'."
                )
            self._nodes[clean_tenant][node.node_id] = copy.deepcopy(node)
            count += 1
        return count

    def upsert_edges(self, edges: List[RelationEdge], tenant_id: str) -> int:
        """Upserts a list of relationship edges within the specified tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.upsert_edges.tenant_id")
        count = 0
        for edge in edges:
            if edge.tenant_id != clean_tenant:
                raise TenantBoundaryError(
                    f"RelationEdge '{edge.edge_id}' tenant_id '{edge.tenant_id}' conflicts with operation tenant_id '{clean_tenant}'."
                )

            # If edge already existed, clean up previous adjacency entries
            if edge.edge_id in self._edges[clean_tenant]:
                prev_edge = self._edges[clean_tenant][edge.edge_id]
                if edge.edge_id in self._out_edges[clean_tenant][prev_edge.source_id]:
                    self._out_edges[clean_tenant][prev_edge.source_id].remove(edge.edge_id)
                if edge.edge_id in self._in_edges[clean_tenant][prev_edge.target_id]:
                    self._in_edges[clean_tenant][prev_edge.target_id].remove(edge.edge_id)

            self._edges[clean_tenant][edge.edge_id] = copy.deepcopy(edge)
            if edge.edge_id not in self._out_edges[clean_tenant][edge.source_id]:
                self._out_edges[clean_tenant][edge.source_id].append(edge.edge_id)
            if edge.edge_id not in self._in_edges[clean_tenant][edge.target_id]:
                self._in_edges[clean_tenant][edge.target_id].append(edge.edge_id)
            count += 1
        return count

    def upsert_graph(self, graph: KnowledgeGraph, tenant_id: str) -> Tuple[int, int]:
        """Upserts a complete KnowledgeGraph within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.upsert_graph.tenant_id")
        if graph.tenant_id != clean_tenant:
            raise TenantBoundaryError(
                f"KnowledgeGraph tenant_id '{graph.tenant_id}' conflicts with operation tenant_id '{clean_tenant}'."
            )
        node_count = self.upsert_nodes(list(graph.nodes.values()), clean_tenant)
        edge_count = self.upsert_edges(list(graph.edges.values()), clean_tenant)
        return (node_count, edge_count)

    def get_node(self, node_id: str, tenant_id: str) -> Optional[EntityNode]:
        """Retrieves an entity node by ID scoped strictly to tenant_id."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.get_node.tenant_id")
        node = self._nodes[clean_tenant].get(node_id)
        return copy.deepcopy(node) if node is not None else None

    def contains_nodes(self, node_ids: List[str], tenant_id: str) -> Set[str]:
        """Returns the subset of node_ids that currently exist within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.contains_nodes.tenant_id")
        tenant_nodes = self._nodes[clean_tenant]
        return {nid for nid in node_ids if nid in tenant_nodes}

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
        """Retrieves adjacent neighbors for a given node within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.get_neighbors.tenant_id")
        if direction not in ("in", "out", "both"):
            raise GraphQueryError(f"direction must be 'in', 'out', or 'both'. Got: {direction!r}")
        if max_depth < 0:
            raise GraphQueryError(f"max_depth must be >= 0. Got: {max_depth}")
        if max_nodes <= 0 or max_edges <= 0:
            raise GraphQueryError("max_nodes and max_edges must be > 0.")

        if node_id not in self._nodes[clean_tenant]:
            return []

        rel_filter = set(relationship_types) if relationship_types else None
        candidate_edges: List[Tuple[RelationEdge, EntityNode]] = []

        # Outgoing edges
        if direction in ("out", "both"):
            for eid in self._out_edges[clean_tenant].get(node_id, []):
                edge = self._edges[clean_tenant].get(eid)
                if edge and (rel_filter is None or edge.relationship_type in rel_filter):
                    target_node = self._nodes[clean_tenant].get(edge.target_id)
                    if target_node:
                        candidate_edges.append((edge, target_node))

        # Incoming edges
        if direction in ("in", "both"):
            for eid in self._in_edges[clean_tenant].get(node_id, []):
                edge = self._edges[clean_tenant].get(eid)
                if edge and (rel_filter is None or edge.relationship_type in rel_filter):
                    source_node = self._nodes[clean_tenant].get(edge.source_id)
                    if source_node:
                        candidate_edges.append((edge, source_node))

        # Deterministic sorting: (relationship_type, neighbor_node_id, edge_id)
        candidate_edges.sort(key=lambda t: (t[0].relationship_type, t[1].node_id, t[0].edge_id))

        if len(candidate_edges) > max_edges or len(candidate_edges) > max_nodes:
            if strict_limits:
                raise GraphQueryError(
                    f"Expansion limits exceeded: {len(candidate_edges)} candidate neighbors found."
                )
            limit = min(max_edges, max_nodes)
            candidate_edges = candidate_edges[:limit]

        return [(copy.deepcopy(e), copy.deepcopy(n)) for e, n in candidate_edges]

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
        """Performs a multi-hop graph traversal starting from start_node_ids."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.traverse.tenant_id")
        if direction not in ("in", "out", "both"):
            raise GraphQueryError(f"direction must be 'in', 'out', or 'both'. Got: {direction!r}")
        if strategy not in ("bfs", "dfs"):
            raise GraphQueryError(f"strategy must be 'bfs' or 'dfs'. Got: {strategy!r}")
        if max_depth < 0:
            raise GraphQueryError(f"max_depth must be >= 0. Got: {max_depth}")
        if max_nodes <= 0 or max_edges <= 0:
            raise GraphQueryError("max_nodes and max_edges must be > 0.")

        rel_filter = set(relationship_types) if relationship_types else None
        collected_nodes: Dict[str, EntityNode] = {}
        collected_edges: Dict[str, RelationEdge] = {}
        is_truncated: bool = False

        # Filter initial start nodes
        initial_nodes = [
            nid for nid in start_node_ids if nid in self._nodes[clean_tenant]
        ]
        # Sort initial nodes deterministically
        initial_nodes.sort()

        for nid in initial_nodes:
            if len(collected_nodes) >= max_nodes:
                if strict_limits:
                    raise GraphQueryError(f"Traversal node limit ({max_nodes}) exceeded at start nodes.")
                is_truncated = True
                break
            collected_nodes[nid] = copy.deepcopy(self._nodes[clean_tenant][nid])

        if max_depth == 0 or is_truncated:
            return KnowledgeGraph(
                tenant_id=clean_tenant,
                nodes=collected_nodes,
                edges=collected_edges,
                metadata={
                    "is_truncated": is_truncated,
                    "strategy": strategy,
                    "depth": max_depth,
                },
            )

        # Queue / Stack: (current_node_id, current_depth)
        # Visited tracking for cycle detection
        visited_nodes: Set[str] = set(collected_nodes.keys())

        if strategy == "bfs":
            queue: deque[Tuple[str, int]] = deque((nid, 0) for nid in collected_nodes.keys())

            while queue:
                current_id, current_depth = queue.popleft()
                if current_depth >= max_depth:
                    continue

                # Find edges according to direction
                incident_edges: List[Tuple[RelationEdge, str]] = []

                if direction in ("out", "both"):
                    for eid in self._out_edges[clean_tenant].get(current_id, []):
                        edge = self._edges[clean_tenant].get(eid)
                        if edge and (rel_filter is None or edge.relationship_type in rel_filter):
                            incident_edges.append((edge, edge.target_id))

                if direction in ("in", "both"):
                    for eid in self._in_edges[clean_tenant].get(current_id, []):
                        edge = self._edges[clean_tenant].get(eid)
                        if edge and (rel_filter is None or edge.relationship_type in rel_filter):
                            incident_edges.append((edge, edge.source_id))

                # Deterministic sorting: (relationship_type, target/neighbor_id, edge_id)
                incident_edges.sort(key=lambda t: (t[0].relationship_type, t[1], t[0].edge_id))

                for edge, neighbor_id in incident_edges:
                    if neighbor_id not in self._nodes[clean_tenant]:
                        continue

                    # Check edge limits
                    if edge.edge_id not in collected_edges:
                        if len(collected_edges) >= max_edges:
                            if strict_limits:
                                raise GraphQueryError(f"Traversal edge limit ({max_edges}) exceeded.")
                            is_truncated = True
                            break
                        collected_edges[edge.edge_id] = copy.deepcopy(edge)

                    # Check node limits
                    if neighbor_id not in collected_nodes:
                        if len(collected_nodes) >= max_nodes:
                            if strict_limits:
                                raise GraphQueryError(f"Traversal node limit ({max_nodes}) exceeded.")
                            is_truncated = True
                            break
                        collected_nodes[neighbor_id] = copy.deepcopy(self._nodes[clean_tenant][neighbor_id])

                    # Cycle detection: only enqueue if neighbor not yet expanded in queue
                    if neighbor_id not in visited_nodes:
                        visited_nodes.add(neighbor_id)
                        queue.append((neighbor_id, current_depth + 1))

                if is_truncated:
                    break
        else:
            # DFS
            stack: List[Tuple[str, int]] = [(nid, 0) for nid in reversed(list(collected_nodes.keys()))]

            while stack:
                current_id, current_depth = stack.pop()
                if current_depth >= max_depth:
                    continue

                incident_edges: List[Tuple[RelationEdge, str]] = []

                if direction in ("out", "both"):
                    for eid in self._out_edges[clean_tenant].get(current_id, []):
                        edge = self._edges[clean_tenant].get(eid)
                        if edge and (rel_filter is None or edge.relationship_type in rel_filter):
                            incident_edges.append((edge, edge.target_id))

                if direction in ("in", "both"):
                    for eid in self._in_edges[clean_tenant].get(current_id, []):
                        edge = self._edges[clean_tenant].get(eid)
                        if edge and (rel_filter is None or edge.relationship_type in rel_filter):
                            incident_edges.append((edge, edge.source_id))

                # For DFS, reverse deterministic sort so that pop() processes in forward order
                incident_edges.sort(key=lambda t: (t[0].relationship_type, t[1], t[0].edge_id), reverse=True)

                for edge, neighbor_id in incident_edges:
                    if neighbor_id not in self._nodes[clean_tenant]:
                        continue

                    if edge.edge_id not in collected_edges:
                        if len(collected_edges) >= max_edges:
                            if strict_limits:
                                raise GraphQueryError(f"Traversal edge limit ({max_edges}) exceeded.")
                            is_truncated = True
                            break
                        collected_edges[edge.edge_id] = copy.deepcopy(edge)

                    if neighbor_id not in collected_nodes:
                        if len(collected_nodes) >= max_nodes:
                            if strict_limits:
                                raise GraphQueryError(f"Traversal node limit ({max_nodes}) exceeded.")
                            is_truncated = True
                            break
                        collected_nodes[neighbor_id] = copy.deepcopy(self._nodes[clean_tenant][neighbor_id])

                    if neighbor_id not in visited_nodes:
                        visited_nodes.add(neighbor_id)
                        stack.append((neighbor_id, current_depth + 1))

                if is_truncated:
                    break

        return KnowledgeGraph(
            tenant_id=clean_tenant,
            nodes=collected_nodes,
            edges=collected_edges,
            metadata={
                "is_truncated": is_truncated,
                "strategy": strategy,
                "depth": max_depth,
            },
        )

    def delete_by_tenant(self, tenant_id: str) -> int:
        """Deletes all graph nodes and edges belonging strictly to the specified tenant."""
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.delete_by_tenant.tenant_id")
        node_count = len(self._nodes[clean_tenant])
        edge_count = len(self._edges[clean_tenant])
        self._nodes.pop(clean_tenant, None)
        self._edges.pop(clean_tenant, None)
        self._out_edges.pop(clean_tenant, None)
        self._in_edges.pop(clean_tenant, None)
        return node_count + edge_count

    def delete_by_document(self, document_id: str, tenant_id: str) -> int:
        """Reconciles and purges graph entities and edges associated with document_id.
        
        5-Step Reconciliation:
        1. Identify chunk nodes owned by document_id (D_chunks). Delete them and incident edges.
        2. Delete document node canonical_document_node_id(tenant_id, document_id).
        3. Reconcile surviving entity nodes: remove document_id & D_chunks; delete if orphaned.
        4. Reconcile surviving relation edges: remove document_id & D_chunks; prune provenance;
           delete if orphaned; update edge weight to max(provenance confidence).
        5. Return count of purged nodes + edges.
        """
        clean_tenant = _validate_tenant_id(tenant_id, "InMemoryGraphStore.delete_by_document.tenant_id")
        if not document_id or not isinstance(document_id, str):
            raise ValueError("document_id must be a non-empty string.")

        purged_nodes_count = 0
        purged_edges_count = 0

        tenant_nodes = self._nodes[clean_tenant]
        tenant_edges = self._edges[clean_tenant]

        # Helper to safely remove edge from adjacency
        def _remove_edge_from_adjacency(edge_id: str, src_id: str, tgt_id: str) -> None:
            if edge_id in self._out_edges[clean_tenant].get(src_id, []):
                self._out_edges[clean_tenant][src_id].remove(edge_id)
            if edge_id in self._in_edges[clean_tenant].get(tgt_id, []):
                self._in_edges[clean_tenant][tgt_id].remove(edge_id)

        # Helper to purge an edge
        def _purge_edge(edge_id: str) -> None:
            nonlocal purged_edges_count
            if edge_id in tenant_edges:
                e = tenant_edges.pop(edge_id)
                _remove_edge_from_adjacency(edge_id, e.source_id, e.target_id)
                purged_edges_count += 1

        # Step 1: Identify all chunk nodes owned by document_id
        chunk_node_ids_to_delete: List[str] = []
        d_chunks: Set[str] = set()

        for nid, node in list(tenant_nodes.items()):
            if node.entity_type == "chunk" and document_id in node.document_ids:
                chunk_node_ids_to_delete.append(nid)
                d_chunks.add(node.entity_id)

        # Delete chunk nodes and incident edges
        for cnid in chunk_node_ids_to_delete:
            tenant_nodes.pop(cnid, None)
            purged_nodes_count += 1

            for eid in list(self._out_edges[clean_tenant].get(cnid, [])):
                _purge_edge(eid)
            for eid in list(self._in_edges[clean_tenant].get(cnid, [])):
                _purge_edge(eid)

        # Step 2: Delete document node
        doc_node_id = canonical_document_node_id(clean_tenant, document_id)
        if doc_node_id in tenant_nodes:
            tenant_nodes.pop(doc_node_id, None)
            purged_nodes_count += 1
            for eid in list(self._out_edges[clean_tenant].get(doc_node_id, [])):
                _purge_edge(eid)
            for eid in list(self._in_edges[clean_tenant].get(doc_node_id, [])):
                _purge_edge(eid)

        # Step 3: Reconcile surviving entity nodes
        entity_node_ids_to_delete: List[str] = []
        for nid, node in list(tenant_nodes.items()):
            if document_id in node.document_ids:
                node.document_ids = [d for d in node.document_ids if d != document_id]
            # Reconcile chunk references
            node.chunk_ids = [cid for cid in node.chunk_ids if cid not in d_chunks]

            # If orphaned (no owning documents left), delete
            if len(node.document_ids) == 0:
                entity_node_ids_to_delete.append(nid)

        for enid in entity_node_ids_to_delete:
            tenant_nodes.pop(enid, None)
            purged_nodes_count += 1
            for eid in list(self._out_edges[clean_tenant].get(enid, [])):
                _purge_edge(eid)
            for eid in list(self._in_edges[clean_tenant].get(enid, [])):
                _purge_edge(eid)

        # Step 4: Reconcile surviving relation edges
        edge_ids_to_delete: List[str] = []
        for eid, edge in list(tenant_edges.items()):
            # If source or target node was purged, edge cannot survive
            if edge.source_id not in tenant_nodes or edge.target_id not in tenant_nodes:
                edge_ids_to_delete.append(eid)
                continue

            if document_id in edge.document_ids:
                edge.document_ids = [d for d in edge.document_ids if d != document_id]
            edge.chunk_ids = [cid for cid in edge.chunk_ids if cid not in d_chunks]
            edge.provenance = [p for p in edge.provenance if p.document_id != document_id]

            if len(edge.document_ids) == 0 or len(edge.provenance) == 0:
                edge_ids_to_delete.append(eid)
            else:
                edge.weight = max([p.confidence for p in edge.provenance], default=1.0)

        for eid in edge_ids_to_delete:
            _purge_edge(eid)

        return purged_nodes_count + purged_edges_count
