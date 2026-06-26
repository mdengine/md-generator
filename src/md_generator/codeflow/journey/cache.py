"""Multi-tier caching for journey traversal performance.

Caches subtrees, successor lists, graph-index lookups, and statistics
to avoid redundant work when traversing large repositories.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from md_generator.codeflow.journey.ir import JourneyNodeIR, JourneyStatistics


class JourneyCache:
    """Multi-tier LRU cache for journey builder performance (Improvement 14).

    Tiers:
    * **Subtree cache** — ``node_id → JourneyNodeIR`` for reuse across branches.
    * **Traversal cache** — ``node_id → [successor_ids]`` to avoid repeated
      graph neighbour lookups.
    * **Statistics cache** — ``node_id → JourneyStatistics`` for subtrees.
    * **Graph-index cache** — ``node_id → {attr_dict}`` for O(1) attribute lookup.
    * **LRU** — global eviction wrapper over the subtree cache.
    """

    def __init__(
        self,
        max_subtree_size: int = 10_000,
        max_lru_size: int = 5_000,
    ) -> None:
        self._max_subtree = max_subtree_size
        self._max_lru = max_lru_size
        self._subtree_cache: dict[str, JourneyNodeIR] = {}
        self._traversal_cache: dict[str, list[str]] = {}
        self._statistics_cache: dict[str, JourneyStatistics] = {}
        self._graph_index: dict[str, dict[str, Any]] = {}
        self._lru: OrderedDict[str, bool] = OrderedDict()
        # Counters
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Subtree cache
    # ------------------------------------------------------------------

    def get_subtree(self, node_id: str) -> JourneyNodeIR | None:
        node = self._subtree_cache.get(node_id)
        if node is not None:
            self._hits += 1
            # Touch LRU
            if node_id in self._lru:
                self._lru.move_to_end(node_id)
        else:
            self._misses += 1
        return node

    def put_subtree(self, node_id: str, subtree: JourneyNodeIR) -> None:
        if len(self._subtree_cache) >= self._max_subtree:
            self._evict_lru()
        self._subtree_cache[node_id] = subtree
        self._lru[node_id] = True
        self._lru.move_to_end(node_id)

    # ------------------------------------------------------------------
    # Traversal cache (successor lists)
    # ------------------------------------------------------------------

    def get_successors(self, node_id: str) -> list[str] | None:
        return self._traversal_cache.get(node_id)

    def put_successors(self, node_id: str, succs: list[str]) -> None:
        self._traversal_cache[node_id] = succs

    # ------------------------------------------------------------------
    # Statistics cache
    # ------------------------------------------------------------------

    def get_statistics(self, node_id: str) -> JourneyStatistics | None:
        return self._statistics_cache.get(node_id)

    def put_statistics(self, node_id: str, stats: JourneyStatistics) -> None:
        self._statistics_cache[node_id] = stats

    # ------------------------------------------------------------------
    # Graph-index cache
    # ------------------------------------------------------------------

    def get_node_attrs(self, node_id: str) -> dict[str, Any] | None:
        return self._graph_index.get(node_id)

    def warm_graph_index(self, g: Any) -> None:
        """Pre-load node attributes from the graph for O(1) lookup."""
        for n, d in g.nodes(data=True):
            self._graph_index[str(n)] = dict(d)

    # ------------------------------------------------------------------
    # LRU eviction
    # ------------------------------------------------------------------

    def _evict_lru(self) -> None:
        while len(self._lru) > self._max_lru:
            oldest, _ = self._lru.popitem(last=False)
            self._subtree_cache.pop(oldest, None)

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self._subtree_cache.clear()
        self._traversal_cache.clear()
        self._statistics_cache.clear()
        self._graph_index.clear()
        self._lru.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict[str, int]:
        return {
            "subtree_size": len(self._subtree_cache),
            "traversal_size": len(self._traversal_cache),
            "statistics_size": len(self._statistics_cache),
            "graph_index_size": len(self._graph_index),
            "hits": self._hits,
            "misses": self._misses,
        }
