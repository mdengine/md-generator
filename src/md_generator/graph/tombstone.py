from __future__ import annotations

"""Tombstone Manager for Deleted Graph Elements & Tombstone Synchronization.

Phase 2C/Prompt 05 Implementation:
- Records and tracks tombstones for deleted documents, chunks, nodes, and edges.
- Prevents resurrection of deleted elements during distributed or incremental sync.
- Thread-safe, multi-tenant partitioned storage with expiration purging.
"""

from dataclasses import dataclass
import threading
import time
from typing import Any, Dict, List, Optional, Set

from md_generator.graph.model import GraphTombstone, _validate_tenant_id


class TombstoneManager:
    """Multi-tenant manager for tracking and querying deletion tombstones."""

    def __init__(self) -> None:
        # tenant_id -> tombstone_id -> GraphTombstone
        self._tombstones: Dict[str, Dict[str, GraphTombstone]] = {}
        # tenant_id -> target_id -> set of tombstone_ids
        self._target_index: Dict[str, Dict[str, Set[str]]] = {}
        self._lock = threading.RLock()

    def record_tombstone(self, tombstone: GraphTombstone) -> None:
        """Records a single deletion tombstone within its tenant boundary."""
        clean_tenant = _validate_tenant_id(tombstone.tenant_id, "TombstoneManager.record_tombstone.tenant_id")
        with self._lock:
            if clean_tenant not in self._tombstones:
                self._tombstones[clean_tenant] = {}
                self._target_index[clean_tenant] = {}

            tid = tombstone.tombstone_id
            self._tombstones[clean_tenant][tid] = tombstone

            target = tombstone.target_id
            if target not in self._target_index[clean_tenant]:
                self._target_index[clean_tenant][target] = set()
            self._target_index[clean_tenant][target].add(tid)

    def record_tombstones(self, tombstones: List[GraphTombstone]) -> None:
        """Records a batch of deletion tombstones."""
        for t in tombstones:
            self.record_tombstone(t)

    def is_tombstoned(self, target_id: str, tenant_id: str) -> bool:
        """Checks if a document, chunk, node, or edge ID is currently tombstoned."""
        clean_tenant = _validate_tenant_id(tenant_id, "TombstoneManager.is_tombstoned.tenant_id")
        with self._lock:
            if clean_tenant not in self._target_index:
                return False
            return target_id in self._target_index[clean_tenant] and bool(
                self._target_index[clean_tenant][target_id]
            )

    def get_tombstones(
        self,
        tenant_id: str,
        target_type: Optional[str] = None,
    ) -> List[GraphTombstone]:
        """Retrieves all tombstones for a tenant, optionally filtered by target_type."""
        clean_tenant = _validate_tenant_id(tenant_id, "TombstoneManager.get_tombstones.tenant_id")
        with self._lock:
            tenant_tombstones = self._tombstones.get(clean_tenant, {})
            if target_type is None:
                return list(tenant_tombstones.values())
            return [
                t for t in tenant_tombstones.values()
                if t.target_type == target_type
            ]

    def purge_expired(self, tenant_id: str, max_age_seconds: float) -> int:
        """Purges tombstones older than max_age_seconds from current time."""
        clean_tenant = _validate_tenant_id(tenant_id, "TombstoneManager.purge_expired.tenant_id")
        now = time.time()
        purged = 0
        with self._lock:
            if clean_tenant not in self._tombstones:
                return 0
            to_delete: List[str] = []
            for tid, t in self._tombstones[clean_tenant].items():
                if now - t.timestamp > max_age_seconds:
                    to_delete.append(tid)

            for tid in to_delete:
                tomb = self._tombstones[clean_tenant].pop(tid)
                tgt = tomb.target_id
                if tgt in self._target_index[clean_tenant]:
                    self._target_index[clean_tenant][tgt].discard(tid)
                    if not self._target_index[clean_tenant][tgt]:
                        self._target_index[clean_tenant].pop(tgt, None)
                purged += 1

        return purged

    def clear_tenant(self, tenant_id: str) -> int:
        """Clears all tombstones for a given tenant."""
        clean_tenant = _validate_tenant_id(tenant_id, "TombstoneManager.clear_tenant.tenant_id")
        with self._lock:
            count = len(self._tombstones.get(clean_tenant, {}))
            self._tombstones.pop(clean_tenant, None)
            self._target_index.pop(clean_tenant, None)
            return count
