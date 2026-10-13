from __future__ import annotations

"""Production Neo4jGraphStore with Cypher Parameterization & Fallback Management.

Phase 2C Implementation: Enterprise Neo4j graph storage, driver lifecycle management,
strict Cypher parameterization, structural identifier regex whitelisting,
idempotent MERGE operations, and explicit fallback policy (no silent downgrade).
"""

import importlib.util
import json
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union

from md_generator.graph.exceptions import (
    GraphQueryError,
    GraphStoreError,
    Neo4jDependencyError,
    TenantBoundaryError,
)
from md_generator.graph.model import (
    EntityNode,
    KnowledgeGraph,
    RelationEdge,
    _validate_tenant_id,
    canonical_document_node_id,
    RELATIONSHIP_TYPE_REGEX,
    EdgeProvenance,
)
from md_generator.graph.protocol import GraphStore
from md_generator.graph.stores.in_memory import InMemoryGraphStore


def _is_neo4j_available() -> bool:
    """Checks whether the neo4j Python driver package is cleanly importable."""
    try:
        spec = importlib.util.find_spec("neo4j")
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        raise Neo4jDependencyError(f"Error checking neo4j package specification: {exc}") from exc


class Neo4jGraphStore(GraphStore):
    """Production graph store backed by Neo4j graph database."""

    def __init__(
        self,
        uri: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
        database: Optional[str] = None,
        driver: Optional[Any] = None,
        fallback_to_memory: bool = False,
    ) -> None:
        self.uri = uri
        self.auth = auth
        self.database = database
        self.fallback_to_memory = fallback_to_memory

        self._fallback_store: Optional[InMemoryGraphStore] = None
        self._driver = driver
        self._owns_driver = driver is None

        # Dependency check
        neo4j_avail = False
        try:
            neo4j_avail = _is_neo4j_available()
        except Neo4jDependencyError:
            if not fallback_to_memory:
                raise
            neo4j_avail = False

        if not neo4j_avail:
            if not fallback_to_memory:
                raise Neo4jDependencyError(
                    "Optional package 'neo4j' is not installed or available. "
                    "Install with 'pip install neo4j' or explicitly configure fallback_to_memory=True."
                )
            self._fallback_store = InMemoryGraphStore()

    def __enter__(self) -> Neo4jGraphStore:
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def initialize(self) -> None:
        """Initializes the Neo4j driver connection and multi-tenant constraints."""
        if self._fallback_store is not None:
            self._fallback_store.initialize()
            return

        if self._driver is None:
            if not self.uri:
                raise GraphStoreError("Neo4j URI must be provided when no pre-existing driver is supplied.")
            try:
                import neo4j
                self.driver_module = neo4j
                auth_tuple = neo4j.basic_auth(self.auth[0], self.auth[1]) if self.auth else None
                self._driver = neo4j.GraphDatabase.driver(self.uri, auth=auth_tuple)
            except Exception as exc:
                if self.fallback_to_memory:
                    self._fallback_store = InMemoryGraphStore()
                    self._fallback_store.initialize()
                    return
                raise GraphStoreError(f"Failed to initialize Neo4j driver: {exc}") from exc

        # Initialize constraints and indexes for tenant isolation and injective IDs
        try:
            with self._get_session() as session:
                session.run(
                    "CREATE CONSTRAINT entity_node_tenant_unique IF NOT EXISTS "
                    "FOR (n:EntityNode) REQUIRE (n.tenant_id, n.node_id) IS UNIQUE"
                )
        except Exception:
            # Tolerant to instances that do not support multi-property constraints (e.g. Neo4j Community)
            pass

    def health_check(self) -> bool:
        """Checks liveness of the graph store."""
        if self._fallback_store is not None:
            return self._fallback_store.health_check()

        if self._driver is None:
            return False

        try:
            with self._get_session() as session:
                result = session.run("RETURN 1 AS alive")
                record = result.single()
                return record is not None and record["alive"] == 1
        except Exception:
            return False

    def close(self) -> None:
        """Closes driver connections and releases pool resources."""
        if self._fallback_store is not None:
            self._fallback_store.close()
            return

        if self._driver is not None and self._owns_driver:
            try:
                self._driver.close()
            except Exception:
                pass
            self._driver = None

    def _get_session(self) -> Any:
        if self._driver is None:
            raise GraphStoreError("Neo4j driver is not initialized. Call initialize() first.")
        if self.database:
            return self._driver.session(database=self.database)
        return self._driver.session()

    def upsert_nodes(self, nodes: List[EntityNode], tenant_id: str) -> int:
        """Upserts entity nodes idempotently using Cypher MERGE within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.upsert_nodes.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.upsert_nodes(nodes, clean_tenant)

        if not nodes:
            return 0

        batch_data = []
        for node in nodes:
            if node.tenant_id != clean_tenant:
                raise TenantBoundaryError(
                    f"EntityNode '{node.node_id}' tenant_id '{node.tenant_id}' conflicts with operation tenant_id '{clean_tenant}'."
                )
            batch_data.append({
                "node_id": node.node_id,
                "entity_id": node.entity_id,
                "entity_type": node.entity_type,
                "name": node.name,
                "qualified_name": node.qualified_name,
                "properties": json.dumps(node.properties),
                "document_ids": list(node.document_ids),
                "chunk_ids": list(node.chunk_ids),
                "source_location": json.dumps(node.source_location.to_dict()) if node.source_location else None,
            })

        query = (
            "UNWIND $batch AS item "
            "MERGE (n:EntityNode {tenant_id: $tenant_id, node_id: item.node_id}) "
            "SET n.entity_id = item.entity_id, "
            "    n.entity_type = item.entity_type, "
            "    n.name = item.name, "
            "    n.qualified_name = item.qualified_name, "
            "    n.properties = item.properties, "
            "    n.document_ids = item.document_ids, "
            "    n.chunk_ids = item.chunk_ids, "
            "    n.source_location = item.source_location "
            "RETURN count(n) AS cnt"
        )

        try:
            with self._get_session() as session:
                result = session.run(query, tenant_id=clean_tenant, batch=batch_data)
                record = result.single()
                return record["cnt"] if record else len(batch_data)
        except Exception as exc:
            raise GraphStoreError(f"Error upserting nodes to Neo4j: {exc}") from exc

    def upsert_edges(self, edges: List[RelationEdge], tenant_id: str) -> int:
        """Upserts relationship edges idempotently within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.upsert_edges.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.upsert_edges(edges, clean_tenant)

        if not edges:
            return 0

        # Group edges by relationship type to ensure valid Cypher identifier injection
        by_rel_type: Dict[str, List[Dict[str, Any]]] = {}
        for edge in edges:
            if edge.tenant_id != clean_tenant:
                raise TenantBoundaryError(
                    f"RelationEdge '{edge.edge_id}' tenant_id '{edge.tenant_id}' conflicts with operation tenant_id '{clean_tenant}'."
                )
            if not RELATIONSHIP_TYPE_REGEX.fullmatch(edge.relationship_type):
                raise GraphQueryError(
                    f"Invalid relationship_type '{edge.relationship_type}'. Must match regex '^[A-Za-z_][A-Za-z0-9_]*$'."
                )

            prov_json = json.dumps([p.to_dict() for p in edge.provenance])
            item = {
                "edge_id": edge.edge_id,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "weight": float(edge.weight),
                "document_ids": list(edge.document_ids),
                "chunk_ids": list(edge.chunk_ids),
                "provenance": prov_json,
                "properties": json.dumps(edge.properties),
            }
            by_rel_type.setdefault(edge.relationship_type, []).append(item)

        total_upserted = 0
        try:
            with self._get_session() as session:
                for rel_type, batch_items in by_rel_type.items():
                    query = (
                        f"UNWIND $batch AS item "
                        f"MATCH (s:EntityNode {{tenant_id: $tenant_id, node_id: item.source_id}}) "
                        f"MATCH (t:EntityNode {{tenant_id: $tenant_id, node_id: item.target_id}}) "
                        f"MERGE (s)-[r:`{rel_type}` {{tenant_id: $tenant_id, edge_id: item.edge_id}}]->(t) "
                        f"SET r.weight = item.weight, "
                        f"    r.document_ids = item.document_ids, "
                        f"    r.chunk_ids = item.chunk_ids, "
                        f"    r.provenance = item.provenance, "
                        f"    r.properties = item.properties "
                        f"RETURN count(r) AS cnt"
                    )
                    result = session.run(query, tenant_id=clean_tenant, batch=batch_items)
                    record = result.single()
                    total_upserted += record["cnt"] if record else len(batch_items)
            return total_upserted
        except Exception as exc:
            raise GraphStoreError(f"Error upserting edges to Neo4j: {exc}") from exc

    def upsert_graph(self, graph: KnowledgeGraph, tenant_id: str) -> Tuple[int, int]:
        """Upserts a complete KnowledgeGraph within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.upsert_graph.tenant_id")
        if graph.tenant_id != clean_tenant:
            raise TenantBoundaryError(
                f"KnowledgeGraph tenant_id '{graph.tenant_id}' conflicts with operation tenant_id '{clean_tenant}'."
            )
        node_count = self.upsert_nodes(list(graph.nodes.values()), clean_tenant)
        edge_count = self.upsert_edges(list(graph.edges.values()), clean_tenant)
        return (node_count, edge_count)

    def _node_from_record(self, record_data: Dict[str, Any], tenant_id: str) -> EntityNode:
        props = json.loads(record_data.get("properties", "{}")) if isinstance(record_data.get("properties"), str) else record_data.get("properties", {})
        loc_data = json.loads(record_data["source_location"]) if record_data.get("source_location") else None
        loc = EntityNode.from_dict({"source_location": loc_data, "node_id": "temp", "tenant_id": tenant_id, "entity_id": "temp", "entity_type": "temp", "name": "temp", "qualified_name": "temp"}).source_location if loc_data else None

        return EntityNode(
            node_id=record_data["node_id"],
            tenant_id=tenant_id,
            entity_id=record_data["entity_id"],
            entity_type=record_data["entity_type"],
            name=record_data["name"],
            qualified_name=record_data["qualified_name"],
            properties=props,
            document_ids=list(record_data.get("document_ids", [])),
            chunk_ids=list(record_data.get("chunk_ids", [])),
            source_location=loc,
        )

    def _edge_from_record(self, record_data: Dict[str, Any], rel_type: str, src_id: str, tgt_id: str, tenant_id: str) -> RelationEdge:
        props = json.loads(record_data.get("properties", "{}")) if isinstance(record_data.get("properties"), str) else record_data.get("properties", {})
        prov_raw = record_data.get("provenance")
        provs = []
        if isinstance(prov_raw, str):
            try:
                prov_list = json.loads(prov_raw)
                provs = [EdgeProvenance.from_dict(p) for p in prov_list]
            except Exception:
                pass

        return RelationEdge(
            edge_id=record_data["edge_id"],
            tenant_id=tenant_id,
            source_id=src_id,
            target_id=tgt_id,
            relationship_type=rel_type,
            weight=float(record_data.get("weight", 1.0)),
            document_ids=list(record_data.get("document_ids", [])),
            chunk_ids=list(record_data.get("chunk_ids", [])),
            provenance=provs,
            properties=props,
        )

    def get_node(self, node_id: str, tenant_id: str) -> Optional[EntityNode]:
        """Retrieves an entity node by ID scoped strictly to tenant_id."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.get_node.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.get_node(node_id, clean_tenant)

        query = (
            "MATCH (n:EntityNode {tenant_id: $tenant_id, node_id: $node_id}) "
            "RETURN properties(n) AS props"
        )
        try:
            with self._get_session() as session:
                result = session.run(query, tenant_id=clean_tenant, node_id=node_id)
                record = result.single()
                if not record:
                    return None
                return self._node_from_record(dict(record["props"]), clean_tenant)
        except Exception as exc:
            raise GraphStoreError(f"Error retrieving node from Neo4j: {exc}") from exc

    def contains_nodes(self, node_ids: List[str], tenant_id: str) -> Set[str]:
        """Returns the subset of node_ids that exist within tenant boundary."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.contains_nodes.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.contains_nodes(node_ids, clean_tenant)

        if not node_ids:
            return set()

        query = (
            "MATCH (n:EntityNode {tenant_id: $tenant_id}) "
            "WHERE n.node_id IN $node_ids "
            "RETURN n.node_id AS node_id"
        )
        try:
            with self._get_session() as session:
                result = session.run(query, tenant_id=clean_tenant, node_ids=node_ids)
                return {record["node_id"] for record in result}
        except Exception as exc:
            raise GraphStoreError(f"Error checking node existence in Neo4j: {exc}") from exc

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
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.get_neighbors.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.get_neighbors(
                node_id=node_id,
                tenant_id=clean_tenant,
                direction=direction,
                relationship_types=relationship_types,
                max_depth=max_depth,
                max_nodes=max_nodes,
                max_edges=max_edges,
                strict_limits=strict_limits,
            )

        if direction not in ("in", "out", "both"):
            raise GraphQueryError(f"direction must be 'in', 'out', or 'both'. Got: {direction!r}")
        if max_depth < 0:
            raise GraphQueryError(f"max_depth must be >= 0. Got: {max_depth}")
        if max_nodes <= 0 or max_edges <= 0:
            raise GraphQueryError("max_nodes and max_edges must be > 0.")

        rel_filter_clause = ""
        if relationship_types:
            for rt in relationship_types:
                if not RELATIONSHIP_TYPE_REGEX.fullmatch(rt):
                    raise GraphQueryError(f"Invalid relationship_type: {rt!r}")
            rel_filter_clause = ":" + "|".join(relationship_types)

        if direction == "out":
            pattern = f"(n)-[r{rel_filter_clause}]->(nbr:EntityNode)"
        elif direction == "in":
            pattern = f"(n)<-[r{rel_filter_clause}]-(nbr:EntityNode)"
        else:
            pattern = f"(n)-[r{rel_filter_clause}]-(nbr:EntityNode)"

        query = (
            f"MATCH (n:EntityNode {{tenant_id: $tenant_id, node_id: $node_id}}) "
            f"MATCH {pattern} "
            f"WHERE nbr.tenant_id = $tenant_id AND r.tenant_id = $tenant_id "
            f"RETURN properties(r) AS r_props, type(r) AS r_type, startNode(r).node_id AS src_id, endNode(r).node_id AS tgt_id, properties(nbr) AS nbr_props "
            f"ORDER BY type(r) ASC, nbr.node_id ASC, r.edge_id ASC"
        )

        try:
            with self._get_session() as session:
                result = session.run(query, tenant_id=clean_tenant, node_id=node_id)
                records = list(result)

                if len(records) > max_edges or len(records) > max_nodes:
                    if strict_limits:
                        raise GraphQueryError(
                            f"Expansion limits exceeded: {len(records)} candidate neighbors found."
                        )
                    limit = min(max_edges, max_nodes)
                    records = records[:limit]

                neighbors: List[Tuple[RelationEdge, EntityNode]] = []
                for rec in records:
                    nbr_node = self._node_from_record(dict(rec["nbr_props"]), clean_tenant)
                    edge = self._edge_from_record(
                        dict(rec["r_props"]),
                        rec["r_type"],
                        rec["src_id"],
                        rec["tgt_id"],
                        clean_tenant,
                    )
                    neighbors.append((edge, nbr_node))
                return neighbors
        except GraphQueryError:
            raise
        except Exception as exc:
            raise GraphStoreError(f"Error retrieving neighbors from Neo4j: {exc}") from exc

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
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.traverse.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.traverse(
                start_node_ids=start_node_ids,
                tenant_id=clean_tenant,
                max_depth=max_depth,
                relationship_types=relationship_types,
                direction=direction,
                strategy=strategy,
                max_nodes=max_nodes,
                max_edges=max_edges,
                strict_limits=strict_limits,
            )

        if direction not in ("in", "out", "both"):
            raise GraphQueryError(f"direction must be 'in', 'out', or 'both'. Got: {direction!r}")
        if strategy not in ("bfs", "dfs"):
            raise GraphQueryError(f"strategy must be 'bfs' or 'dfs'. Got: {strategy!r}")
        if max_depth < 0:
            raise GraphQueryError(f"max_depth must be >= 0. Got: {max_depth}")
        if max_nodes <= 0 or max_edges <= 0:
            raise GraphQueryError("max_nodes and max_edges must be > 0.")

        rel_filter_clause = ""
        if relationship_types:
            for rt in relationship_types:
                if not RELATIONSHIP_TYPE_REGEX.fullmatch(rt):
                    raise GraphQueryError(f"Invalid relationship_type: {rt!r}")
            rel_filter_clause = ":" + "|".join(relationship_types)

        if direction == "out":
            pattern = f"(s)-[r{rel_filter_clause}*0..{max_depth}]->(m:EntityNode)"
        elif direction == "in":
            pattern = f"(s)<-[r{rel_filter_clause}*0..{max_depth}]-(m:EntityNode)"
        else:
            pattern = f"(s)-[r{rel_filter_clause}*0..{max_depth}]-(m:EntityNode)"

        query = (
            f"MATCH (s:EntityNode {{tenant_id: $tenant_id}}) "
            f"WHERE s.node_id IN $start_node_ids "
            f"MATCH path = {pattern} "
            f"WHERE all(n IN nodes(path) WHERE n.tenant_id = $tenant_id) "
            f"  AND all(rel IN relationships(path) WHERE rel.tenant_id = $tenant_id) "
            f"WITH nodes(path) AS ns, relationships(path) AS rs "
            f"UNWIND ns AS n "
            f"WITH collect(DISTINCT n) AS all_nodes, rs "
            f"UNWIND rs AS r "
            f"RETURN all_nodes, collect(DISTINCT r) AS all_edges"
        )

        try:
            with self._get_session() as session:
                result = session.run(query, tenant_id=clean_tenant, start_node_ids=start_node_ids)
                record = result.single()

                collected_nodes: Dict[str, EntityNode] = {}
                collected_edges: Dict[str, RelationEdge] = {}
                is_truncated = False

                if record:
                    raw_nodes = record["all_nodes"] or []
                    raw_edges = record["all_edges"] or []

                    if len(raw_nodes) > max_nodes or len(raw_edges) > max_edges:
                        if strict_limits:
                            raise GraphQueryError("Traversal exceeded node or edge limits.")
                        is_truncated = True

                    for n in raw_nodes[:max_nodes]:
                        props = dict(n)
                        node = self._node_from_record(props, clean_tenant)
                        collected_nodes[node.node_id] = node

                    for r in raw_edges[:max_edges]:
                        props = dict(r)
                        edge = self._edge_from_record(
                            props,
                            r.type,
                            r.start_node["node_id"],
                            r.end_node["node_id"],
                            clean_tenant,
                        )
                        collected_edges[edge.edge_id] = edge

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
        except GraphQueryError:
            raise
        except Exception as exc:
            raise GraphStoreError(f"Error during Neo4j traversal: {exc}") from exc

    def delete_by_tenant(self, tenant_id: str) -> int:
        """Deletes all graph nodes and edges belonging strictly to the specified tenant."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.delete_by_tenant.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.delete_by_tenant(clean_tenant)

        query = (
            "MATCH (n:EntityNode {tenant_id: $tenant_id}) "
            "WITH count(n) AS cnt, collect(n) AS nodes "
            "FOREACH (x IN nodes | DETACH DELETE x) "
            "RETURN cnt"
        )
        try:
            with self._get_session() as session:
                result = session.run(query, tenant_id=clean_tenant)
                record = result.single()
                return record["cnt"] if record else 0
        except Exception as exc:
            raise GraphStoreError(f"Error deleting tenant in Neo4j: {exc}") from exc

    def delete_by_document(self, document_id: str, tenant_id: str) -> int:
        """Reconciles and purges graph entities and edges associated with document_id."""
        clean_tenant = _validate_tenant_id(tenant_id, "Neo4jGraphStore.delete_by_document.tenant_id")
        if self._fallback_store is not None:
            return self._fallback_store.delete_by_document(document_id, clean_tenant)

        if not document_id or not isinstance(document_id, str):
            raise ValueError("document_id must be a non-empty string.")

        # Cypher reconciliation executing the 5-step contract in transaction
        step1_chunk_query = (
            "MATCH (c:EntityNode {tenant_id: $tenant_id, entity_type: 'chunk'}) "
            "WHERE $document_id IN c.document_ids "
            "WITH collect(c.entity_id) AS d_chunks, collect(c) AS chunk_nodes "
            "UNWIND chunk_nodes AS cn "
            "DETACH DELETE cn "
            "RETURN d_chunks, size(chunk_nodes) AS purged_chunks"
        )
        step2_doc_query = (
            "MATCH (d:EntityNode {tenant_id: $tenant_id, node_id: $doc_node_id}) "
            "DETACH DELETE d "
            "RETURN count(d) AS purged_docs"
        )
        step3_entity_query = (
            "MATCH (n:EntityNode {tenant_id: $tenant_id}) "
            "WHERE $document_id IN n.document_ids "
            "SET n.document_ids = [x IN n.document_ids WHERE x <> $document_id], "
            "    n.chunk_ids = [c IN n.chunk_ids WHERE NOT c IN $d_chunks] "
            "WITH n WHERE size(n.document_ids) = 0 "
            "DETACH DELETE n "
            "RETURN count(n) AS orphaned_entities"
        )
        step4_edge_query = (
            "MATCH ()-[r {tenant_id: $tenant_id}]->() "
            "WHERE $document_id IN r.document_ids "
            "SET r.document_ids = [x IN r.document_ids WHERE x <> $document_id], "
            "    r.chunk_ids = [c IN r.chunk_ids WHERE NOT c IN $d_chunks] "
            "WITH r WHERE size(r.document_ids) = 0 "
            "DELETE r "
            "RETURN count(r) AS orphaned_edges"
        )

        doc_node_id = canonical_document_node_id(clean_tenant, document_id)
        total_purged = 0

        try:
            with self._get_session() as session:
                tx = session.begin_transaction()
                tx_obj = tx.__enter__() if hasattr(tx, "__enter__") else tx
                try:
                    res1 = tx_obj.run(step1_chunk_query, tenant_id=clean_tenant, document_id=document_id)
                    rec1 = res1.single()
                    d_chunks = rec1["d_chunks"] if rec1 else []
                    total_purged += (rec1["purged_chunks"] if rec1 else 0)

                    res2 = tx_obj.run(step2_doc_query, tenant_id=clean_tenant, doc_node_id=doc_node_id)
                    rec2 = res2.single()
                    total_purged += (rec2["purged_docs"] if rec2 else 0)

                    res3 = tx_obj.run(step3_entity_query, tenant_id=clean_tenant, document_id=document_id, d_chunks=d_chunks)
                    rec3 = res3.single()
                    total_purged += (rec3["orphaned_entities"] if rec3 else 0)

                    res4 = tx_obj.run(step4_edge_query, tenant_id=clean_tenant, document_id=document_id, d_chunks=d_chunks)
                    rec4 = res4.single()
                    total_purged += (rec4["orphaned_edges"] if rec4 else 0)

                    tx_obj.commit()
                except Exception:
                    if hasattr(tx_obj, "rollback"):
                        tx_obj.rollback()
                    raise
                finally:
                    if hasattr(tx, "__exit__"):
                        try:
                            tx.__exit__(None, None, None)
                        except Exception:
                            pass
                    elif hasattr(tx_obj, "close"):
                        tx_obj.close()
            return total_purged
        except Exception as exc:
            raise GraphStoreError(f"Error executing document reconciliation in Neo4j: {exc}") from exc


class GraphStoreFactory:
    """Factory creating configured graph store implementations."""

    @staticmethod
    def create(
        provider: Literal["in_memory", "neo4j"] = "in_memory",
        uri: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
        database: Optional[str] = None,
        driver: Optional[Any] = None,
        fallback_to_memory: bool = False,
        **kwargs: Any,
    ) -> GraphStore:
        """Creates a GraphStore instance based on the specified provider."""
        if provider == "in_memory":
            return InMemoryGraphStore()
        elif provider == "neo4j":
            return Neo4jGraphStore(
                uri=uri,
                auth=auth,
                database=database,
                driver=driver,
                fallback_to_memory=fallback_to_memory,
            )
        else:
            raise ValueError(f"Unknown graph store provider: {provider!r}. Must be 'in_memory' or 'neo4j'.")
