"""Compute statistics from a ``JourneyIR`` tree.

The ``compute_statistics`` function walks the ``JourneyNodeIR`` tree once and
populates a ``JourneyStatistics`` instance with all 14+ metrics from the spec.
"""

from __future__ import annotations

from collections import defaultdict

from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR, JourneyStatistics


# Node types mapped to semantic categories for counting.
_DB_TYPES = frozenset({"table", "collection", "database"})
_QUEUE_TYPES = frozenset({"topic", "queue"})
_CONFIG_TYPES = frozenset({"config", "configuration"})
_EXTERNAL_TYPES = frozenset({"external", "external_api"})
_FRAMEWORK_TYPES = frozenset({"framework"})


def compute_statistics(ir: JourneyIR) -> JourneyStatistics:
    """Walk ``ir.root`` and fill a fresh ``JourneyStatistics``."""
    stats = JourneyStatistics()
    if ir.root is None:
        return stats

    depths: list[int] = []
    lang: dict[str, int] = defaultdict(int)
    ntype: dict[str, int] = defaultdict(int)
    etype: dict[str, int] = defaultdict(int)
    stop_dist: dict[str, int] = defaultdict(int)

    def _walk(node: JourneyNodeIR) -> None:
        stats.node_count += 1
        depths.append(node.depth)
        if node.depth > stats.maximum_depth:
            stats.maximum_depth = node.depth

        # Language distribution
        if node.language:
            lang[node.language] += 1

        # Node type distribution
        nt = node.node_type or "unknown"
        ntype[nt] += 1

        # Edge type distribution (for non-root nodes)
        if node.edge_relation:
            etype[node.edge_relation] += 1
            stats.edge_count += 1

        # Category counters
        nt_lower = nt.lower()
        if nt_lower in _DB_TYPES:
            stats.database_count += 1
        elif nt_lower in _QUEUE_TYPES:
            stats.queue_count += 1
        elif nt_lower in _CONFIG_TYPES:
            stats.configuration_count += 1
        elif nt_lower in _EXTERNAL_TYPES:
            stats.external_api_count += 1

        if node.framework:
            stats.framework_count += 1

        # Cycle / recursion
        if node.is_cycle:
            stats.cycle_count += 1
        if node.is_recursive:
            stats.recursion_count += 1

        # Stop reasons
        if node.stop_reason is not None:
            stop_dist[node.stop_reason.value] += 1
            if node.stop_reason.value in ("max_depth_reached", "max_nodes_reached"):
                stats.truncation_count += 1

        # Leaf / branch
        if node.is_leaf or not node.children:
            stats.leaf_count += 1
        else:
            stats.branch_count += 1

        for child in node.children:
            _walk(child)

    _walk(ir.root)

    stats.average_depth = sum(depths) / len(depths) if depths else 0.0
    stats.language_distribution = dict(lang)
    stats.node_type_distribution = dict(ntype)
    stats.edge_type_distribution = dict(etype)
    stats.stop_reason_distribution = dict(stop_dist)

    # execution_path_count is set externally by paths.py
    if ir.execution_paths is not None:
        stats.execution_path_count = len(ir.execution_paths)

    return stats
