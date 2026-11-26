from __future__ import annotations

"""Incremental Knowledge Graph Engine & Document Lifecycle Reconciliation.

Phase 2C/Prompt 05 Implementation:
- GraphReconciler: incremental diffing, state reconciliation, and synchronization.
- Detects inserted, modified, and deleted nodes and edges.
- Tombstone creation and propagation for deleted documents and chunks.
- Idempotent synchronizations using document version content hashing.
- Atomic staged transactions with snapshot rollback on failure.
- Multi-tenant operational boundary enforcement.
"""

from collections import defaultdict
import copy
from dataclasses import dataclass, field
import hashlib
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    GraphTombstone,
    canonical_document_node_id,
    canonical_chunk_node_id,
    _validate_tenant_id,
)
from md_generator.graph.extractor import extract
from md_generator.graph.entity_extractor import BaseEntityExtractor, RuleBasedEntityExtractor
from md_generator.graph.tombstone import TombstoneManager
from md_generator.graph.protocol import GraphStore
from md_generator.graph.exceptions import GraphError, GraphStoreError, TenantBoundaryError


@dataclass
class ReconciliationDiff:
    """Detailed structural and domain diff generated during incremental graph reconciliation."""
    inserted_nodes: List[EntityNode] = field(default_factory=list)
    modified_nodes: List[EntityNode] = field(default_factory=list)
    deleted_node_ids: List[str] = field(default_factory=list)
    inserted_edges: List[RelationEdge] = field(default_factory=list)
    modified_edges: List[RelationEdge] = field(default_factory=list)
    deleted_edge_ids: List[str] = field(default_factory=list)
    tombstones: List[GraphTombstone] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.inserted_nodes
            or self.modified_nodes
            or self.deleted_node_ids
            or self.inserted_edges
            or self.modified_edges
            or self.deleted_edge_ids
            or self.tombstones
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inserted_nodes_count": len(self.inserted_nodes),
            "modified_nodes_count": len(self.modified_nodes),
            "deleted_node_ids": list(self.deleted_node_ids),
            "inserted_edges_count": len(self.inserted_edges),
            "modified_edges_count": len(self.modified_edges),
            "deleted_edge_ids": list(self.deleted_edge_ids),
            "tombstones_count": len(self.tombstones),
        }


@dataclass
class ReconciliationResult:
    """Outcome of incremental document graph reconciliation."""
    tenant_id: str
    document_id: str
    diff: ReconciliationDiff
    unchanged: bool = False
    current_hash: str = ""
    previous_hash: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "document_id": self.document_id,
            "unchanged": self.unchanged,
            "current_hash": self.current_hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "diff": self.diff.to_dict(),
        }


def compute_document_content_hash(
    semantic_document: SemanticDocument,
    chunks: List[SemanticChunk],
) -> str:
    """Computes a deterministic canonical content hash representing the document state."""
    hasher = hashlib.sha256()
    doc_id = semantic_document.document_id or ""
    hasher.update(doc_id.encode("utf-8"))
    content = semantic_document.sanitized_content or ""
    hasher.update(content.encode("utf-8"))

    # Incorporate sorted chunks
    for c in sorted(chunks, key=lambda x: str(x.chunk_id)):
        cid = c.chunk_id or ""
        c_content = c.sanitized_content or ""
        hasher.update(cid.encode("utf-8"))
        hasher.update(c_content.encode("utf-8"))

    return hasher.hexdigest()


class GraphReconciler:
    """Incremental Knowledge Graph reconciler and synchronizer."""

    def __init__(
        self,
        store: Optional[GraphStore] = None,
        tombstone_manager: Optional[TombstoneManager] = None,
        entity_extractor: Optional[BaseEntityExtractor] = None,
    ) -> None:
        self.store = store
        self.tombstone_manager = tombstone_manager or TombstoneManager()
        self.entity_extractor = entity_extractor or RuleBasedEntityExtractor()
        self._tenant_locks: Dict[str, threading.RLock] = defaultdict(threading.RLock)
        self._global_lock = threading.RLock()

    def _get_tenant_lock(self, tenant_id: str) -> threading.RLock:
        with self._global_lock:
            return self._tenant_locks[tenant_id]

    def snapshot_store(self, tenant_id: str, store: GraphStore) -> Dict[str, Any]:
        """Captures a thread-safe snapshot of tenant store state for atomic rollback."""
        clean_tenant = _validate_tenant_id(tenant_id, "snapshot_store.tenant_id")
        if hasattr(store, "_nodes") and hasattr(store, "_edges"):
            # InMemoryGraphStore
            nodes_copy = {k: copy.deepcopy(v) for k, v in store._nodes.get(clean_tenant, {}).items()}
            edges_copy = {k: copy.deepcopy(v) for k, v in store._edges.get(clean_tenant, {}).items()}
            out_copy = {k: list(v) for k, v in store._out_edges.get(clean_tenant, {}).items()}
            in_copy = {k: list(v) for k, v in store._in_edges.get(clean_tenant, {}).items()}
            return {
                "type": "in_memory",
                "nodes": nodes_copy,
                "edges": edges_copy,
                "out_edges": out_copy,
                "in_edges": in_copy,
            }
        return {"type": "opaque"}

    def restore_store(self, snapshot: Dict[str, Any], tenant_id: str, store: GraphStore) -> None:
        """Restores store state from snapshot upon transaction failure."""
        clean_tenant = _validate_tenant_id(tenant_id, "restore_store.tenant_id")
        if snapshot.get("type") == "in_memory" and hasattr(store, "_nodes"):
            store._nodes[clean_tenant] = snapshot["nodes"]
            store._edges[clean_tenant] = snapshot["edges"]
            store._out_edges[clean_tenant] = defaultdict(list, snapshot["out_edges"])
            store._in_edges[clean_tenant] = defaultdict(list, snapshot["in_edges"])

    def reconcile_document(
        self,
        semantic_document: SemanticDocument,
        chunks: List[SemanticChunk],
        tenant_id: str,
        store: Optional[GraphStore] = None,
        prev_content_hash: Optional[str] = None,
        extract_domain: bool = True,
        extract_structural: bool = True,
    ) -> ReconciliationResult:
        """Performs incremental graph reconciliation for a document and its chunks.
        
        Lifecycle Steps:
        1. Multi-tenant validation and concurrency locking.
        2. Idempotent check: if prev_content_hash matches current_hash, returns no-op result.
        3. Extracts newly targeted KnowledgeGraph for document and chunks.
        4. Gathers existing document and chunk graph elements from store.
        5. Computes delta: inserted, modified, and deleted nodes & edges.
        6. Reconciles shared entities and prunes orphaned graph elements.
        7. Creates and registers deletion tombstones for removed elements.
        8. Atomically applies mutations to store with snapshot rollback safety.
        """
        active_store = store or self.store
        if active_store is None:
            raise GraphStoreError("GraphStore must be provided to GraphReconciler or reconcile_document.")

        clean_tenant = _validate_tenant_id(tenant_id, "reconcile_document.tenant_id")
        doc_id = semantic_document.document_id
        if not doc_id:
            raise GraphError("semantic_document must have a valid document_id.")

        lock = self._get_tenant_lock(clean_tenant)
        with lock:
            # Step 1: Compute hash & check idempotency
            current_hash = compute_document_content_hash(semantic_document, chunks)
            if prev_content_hash and prev_content_hash == current_hash:
                return ReconciliationResult(
                    tenant_id=clean_tenant,
                    document_id=doc_id,
                    diff=ReconciliationDiff(),
                    unchanged=True,
                    current_hash=current_hash,
                    previous_hash=prev_content_hash,
                )

            # Step 2: Extract new target graph for this document
            new_graph = extract(
                semantic_document,
                chunks,
                tenant_id=clean_tenant,
                extract_structural=extract_structural,
                extract_domain=extract_domain,
                entity_extractor=self.entity_extractor,
            )

            # Step 3: Identify existing graph elements owned or referenced by doc_id in store
            existing_doc_nodes: Dict[str, EntityNode] = {}
            existing_doc_edges: Dict[str, RelationEdge] = {}

            if hasattr(active_store, "get_all_nodes") and hasattr(active_store, "get_all_edges"):
                all_nodes = active_store.get_all_nodes(clean_tenant)
                all_edges = active_store.get_all_edges(clean_tenant)
            elif hasattr(active_store, "_nodes") and hasattr(active_store, "_edges"):
                all_nodes = list(active_store._nodes.get(clean_tenant, {}).values())
                all_edges = list(active_store._edges.get(clean_tenant, {}).values())
            else:
                all_nodes = []
                all_edges = []

            for n in all_nodes:
                if doc_id in n.document_ids or f":doc:{doc_id}" in n.node_id:
                    existing_doc_nodes[n.node_id] = copy.deepcopy(n)

            for e in all_edges:
                if doc_id in e.document_ids:
                    existing_doc_edges[e.edge_id] = copy.deepcopy(e)

            # Current chunk IDs in the updated document
            new_chunk_ids: Set[str] = {c.chunk_id for c in chunks if c.chunk_id}

            diff = ReconciliationDiff()

            # Step 4: Reconcile Nodes
            # Nodes present in new_graph
            for nid, new_node in new_graph.nodes.items():
                if nid not in existing_doc_nodes:
                    diff.inserted_nodes.append(new_node)
                else:
                    old_node = existing_doc_nodes[nid]
                    # Check for updates in properties, chunk_ids, or source location
                    has_changed = (
                        old_node.properties != new_node.properties
                        or set(old_node.chunk_ids) != set(new_node.chunk_ids)
                        or old_node.source_location != new_node.source_location
                    )
                    if has_changed:
                        # Merge document_ids to preserve cross-document references
                        combined_doc_ids = sorted(list(set(old_node.document_ids).union(set(new_node.document_ids))))
                        merged_node = copy.deepcopy(new_node)
                        merged_node.document_ids = combined_doc_ids
                        diff.modified_nodes.append(merged_node)

            # Nodes previously associated with doc_id but NOT in new_graph
            for nid, old_node in existing_doc_nodes.items():
                if nid not in new_graph.nodes:
                    # If it's a chunk or structural node belonging to this doc, it was deleted!
                    if old_node.entity_type in ("chunk", "page", "slide", "section", "table", "image"):
                        diff.deleted_node_ids.append(nid)
                        diff.tombstones.append(GraphTombstone(
                            tenant_id=clean_tenant,
                            target_type=old_node.entity_type,
                            target_id=old_node.entity_id,
                            timestamp=time.time(),
                            version_hash=current_hash,
                            reason="chunk_or_structural_deletion",
                        ))
                    else:
                        # Domain entity node: reconcile document_ids and chunk_ids
                        surviving_doc_ids = [d for d in old_node.document_ids if d != doc_id]
                        surviving_chunk_ids = [c for c in old_node.chunk_ids if c in new_chunk_ids]

                        if len(surviving_doc_ids) == 0:
                            # Orphaned domain entity: delete
                            diff.deleted_node_ids.append(nid)
                            diff.tombstones.append(GraphTombstone(
                                tenant_id=clean_tenant,
                                target_type="entity",
                                target_id=old_node.entity_id,
                                timestamp=time.time(),
                                version_hash=current_hash,
                                reason="orphaned_entity",
                            ))
                        else:
                            # Shared entity: update to remove this doc
                            mod_node = copy.deepcopy(old_node)
                            mod_node.document_ids = surviving_doc_ids
                            mod_node.chunk_ids = surviving_chunk_ids
                            diff.modified_nodes.append(mod_node)

            # Step 5: Reconcile Edges
            deleted_nodes_set = set(diff.deleted_node_ids)

            for eid, new_edge in new_graph.edges.items():
                if eid not in existing_doc_edges:
                    diff.inserted_edges.append(new_edge)
                else:
                    old_edge = existing_doc_edges[eid]
                    has_changed = (
                        old_edge.weight != new_edge.weight
                        or old_edge.properties != new_edge.properties
                        or set(old_edge.chunk_ids) != set(new_edge.chunk_ids)
                    )
                    if has_changed:
                        combined_doc_ids = sorted(list(set(old_edge.document_ids).union(set(new_edge.document_ids))))
                        merged_edge = copy.deepcopy(new_edge)
                        merged_edge.document_ids = combined_doc_ids
                        diff.modified_edges.append(merged_edge)

            for eid, old_edge in existing_doc_edges.items():
                # If either endpoint was deleted, edge must be deleted
                if old_edge.source_id in deleted_nodes_set or old_edge.target_id in deleted_nodes_set:
                    diff.deleted_edge_ids.append(eid)
                    diff.tombstones.append(GraphTombstone(
                        tenant_id=clean_tenant,
                        target_type="edge",
                        target_id=old_edge.edge_id,
                        timestamp=time.time(),
                        version_hash=current_hash,
                        reason="endpoint_deleted",
                    ))
                elif eid not in new_graph.edges:
                    # Edge not in new document extraction
                    surviving_doc_ids = [d for d in old_edge.document_ids if d != doc_id]
                    surviving_prov = [p for p in old_edge.provenance if p.document_id != doc_id]

                    if len(surviving_doc_ids) == 0 or len(surviving_prov) == 0:
                        diff.deleted_edge_ids.append(eid)
                        diff.tombstones.append(GraphTombstone(
                            tenant_id=clean_tenant,
                            target_type="edge",
                            target_id=old_edge.edge_id,
                            timestamp=time.time(),
                            version_hash=current_hash,
                            reason="edge_unreferenced",
                        ))
                    else:
                        mod_edge = copy.deepcopy(old_edge)
                        mod_edge.document_ids = surviving_doc_ids
                        mod_edge.provenance = surviving_prov
                        mod_edge.weight = max([p.confidence for p in surviving_prov], default=1.0)
                        diff.modified_edges.append(mod_edge)

            # Step 6: Atomic Store Application with Rollback Checkpoint
            snapshot = self.snapshot_store(clean_tenant, active_store)
            try:
                # 6a. Delete purged edges and nodes
                if hasattr(active_store, "delete_edges") and diff.deleted_edge_ids:
                    active_store.delete_edges(diff.deleted_edge_ids, tenant_id=clean_tenant)
                if hasattr(active_store, "delete_nodes") and diff.deleted_node_ids:
                    active_store.delete_nodes(diff.deleted_node_ids, tenant_id=clean_tenant)

                # 6b. Upsert inserted and modified nodes
                nodes_to_upsert = diff.inserted_nodes + diff.modified_nodes
                if nodes_to_upsert:
                    active_store.upsert_nodes(nodes_to_upsert, tenant_id=clean_tenant)

                # 6c. Upsert inserted and modified edges
                edges_to_upsert = diff.inserted_edges + diff.modified_edges
                if edges_to_upsert:
                    active_store.upsert_edges(edges_to_upsert, tenant_id=clean_tenant)

                # 6d. Register tombstones
                self.tombstone_manager.record_tombstones(diff.tombstones)

            except Exception as e:
                # Rollback to pre-reconciliation snapshot
                self.restore_store(snapshot, clean_tenant, active_store)
                raise GraphStoreError(f"Incremental reconciliation transaction failed: {e}") from e

            return ReconciliationResult(
                tenant_id=clean_tenant,
                document_id=doc_id,
                diff=diff,
                unchanged=False,
                current_hash=current_hash,
                previous_hash=prev_content_hash,
            )

    def delete_document(
        self,
        document_id: str,
        tenant_id: str,
        store: Optional[GraphStore] = None,
        version_hash: str = "",
    ) -> ReconciliationResult:
        """Deletes a document from the graph, creates tombstones, and prunes orphaned graph elements."""
        active_store = store or self.store
        if active_store is None:
            raise GraphStoreError("GraphStore must be provided to GraphReconciler or delete_document.")

        clean_tenant = _validate_tenant_id(tenant_id, "delete_document.tenant_id")
        if not document_id or not isinstance(document_id, str):
            raise ValueError("document_id must be a non-empty string.")

        lock = self._get_tenant_lock(clean_tenant)
        with lock:
            # 1. Identify chunk nodes owned by this document before purging
            owned_chunk_ids: List[str] = []
            if hasattr(active_store, "get_all_nodes"):
                nodes = active_store.get_all_nodes(clean_tenant)
                for n in nodes:
                    if n.entity_type == "chunk" and document_id in n.document_ids:
                        owned_chunk_ids.append(n.entity_id)

            # 2. Execute store reconciliation purge
            purged_count = active_store.delete_by_document(document_id, tenant_id=clean_tenant)

            # 3. Create tombstones for document and its chunks
            tombstones: List[GraphTombstone] = [
                GraphTombstone(
                    tenant_id=clean_tenant,
                    target_type="document",
                    target_id=document_id,
                    timestamp=time.time(),
                    version_hash=version_hash,
                    reason="document_deleted",
                )
            ]
            for cid in owned_chunk_ids:
                tombstones.append(GraphTombstone(
                    tenant_id=clean_tenant,
                    target_type="chunk",
                    target_id=cid,
                    timestamp=time.time(),
                    version_hash=version_hash,
                    reason="chunk_deleted",
                ))

            self.tombstone_manager.record_tombstones(tombstones)

            diff = ReconciliationDiff(
                deleted_node_ids=[canonical_document_node_id(clean_tenant, document_id)],
                tombstones=tombstones,
            )

            return ReconciliationResult(
                tenant_id=clean_tenant,
                document_id=document_id,
                diff=diff,
                unchanged=False,
                current_hash="",
                previous_hash=version_hash,
            )
