"""JourneyBuilder — the primary orchestrator for journey construction.

Produces ``JourneyIR`` from the graph.  Each ``build_*_journey`` method:

1. Resolves start node(s)
2. Applies filters (edge → expansion → stop)
3. Delegates to ``traversal.traverse_journey()``
4. Post-processes via ``tree.py`` (collapse chains, prune, shared-subtrees)
5. Optionally enriches with CFG overlay
6. Returns ``JourneyIR``
"""

from __future__ import annotations

from typing import Any

from md_generator.codeflow.graph.multigraph_utils import CodeflowGraph
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.journey.cache import JourneyCache
from md_generator.codeflow.journey.filters import (
    EdgeFilter,
    ExpansionFilter,
    JourneyFilterConfig,
    StopConditionEvaluator,
)
from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR
from md_generator.codeflow.journey.models import JourneyConfig, JourneyType
from md_generator.codeflow.journey.traversal import traverse_journey
from md_generator.codeflow.journey import tree as tree_utils


class JourneyBuilder:
    """Build ``JourneyIR`` instances from a ``CodeflowGraph``."""

    def __init__(
        self,
        query: GraphQuery,
        g: CodeflowGraph,
        config: JourneyConfig,
        filter_config: JourneyFilterConfig | None = None,
    ) -> None:
        self._query = query
        self._g = g
        self._config = config
        self._filter_config = filter_config or JourneyFilterConfig()
        self._edge_filter = EdgeFilter(config, self._filter_config)
        self._expansion_filter = ExpansionFilter(config.expand_strategy)
        self._stop_eval = StopConditionEvaluator(config)
        self._cache = JourneyCache()

    # ------------------------------------------------------------------
    # Core traversal helper
    # ------------------------------------------------------------------

    def _build_single(self, start_id: str, journey_type: JourneyType | None = None) -> JourneyIR:
        """Run traversal + post-processing for a single start node."""
        cfg = self._config
        ir = traverse_journey(
            self._query, self._g, start_id, cfg,
            self._edge_filter, self._expansion_filter, self._stop_eval, self._cache,
        )

        # Override journey type if requested
        if journey_type is not None:
            ir.metadata.journey_type = journey_type

        # Post-process
        if cfg.collapse_linear_chains:
            ir.root = tree_utils.collapse_linear_chains(ir.root)

        ir.root = tree_utils.apply_shared_subtree_mode(ir.root, cfg.shared_subtrees)

        if cfg.effective_max_depth is not None:
            ir.root = tree_utils.prune_below_depth(ir.root, cfg.effective_max_depth)

        # Recompute statistics after post-processing
        from md_generator.codeflow.journey.statistics import compute_statistics
        ir.statistics = compute_statistics(ir)
        ir.metadata.total_nodes = ir.statistics.node_count
        ir.metadata.total_depth = ir.statistics.maximum_depth

        # Enumerate execution paths if requested
        if cfg.enumerate_paths:
            from md_generator.codeflow.journey.paths import enumerate_execution_paths
            ir.execution_paths = enumerate_execution_paths(ir)

        return ir

    # ------------------------------------------------------------------
    # Generic build
    # ------------------------------------------------------------------

    def build(self, start_id: str) -> JourneyIR:
        """Build a journey from an arbitrary start node."""
        return self._build_single(start_id)

    # ------------------------------------------------------------------
    # Type-specific builders
    # ------------------------------------------------------------------

    def build_method_journey(self, symbol_id: str) -> JourneyIR:
        return self._build_single(symbol_id, JourneyType.METHOD)

    def build_class_journey(self, class_node_id: str) -> JourneyIR:
        return self._build_single(class_node_id, JourneyType.CLASS)

    def build_file_journey(self, file_node_id: str) -> JourneyIR:
        return self._build_single(file_node_id, JourneyType.FILE)

    def build_api_journey(self, entry_id: str) -> JourneyIR:
        return self._build_single(entry_id, JourneyType.API)

    def build_event_journey(self, event_node_id: str) -> JourneyIR:
        return self._build_single(event_node_id, JourneyType.EVENT)

    def build_database_journey(self, table_node_id: str) -> JourneyIR:
        return self._build_single(table_node_id, JourneyType.DATABASE)

    def build_queue_journey(self, queue_node_id: str) -> JourneyIR:
        return self._build_single(queue_node_id, JourneyType.QUEUE)

    def build_config_journey(self, config_node_id: str) -> JourneyIR:
        return self._build_single(config_node_id, JourneyType.CONFIG)

    def build_dependency_journey(self, dep_node_id: str) -> JourneyIR:
        return self._build_single(dep_node_id, JourneyType.DEPENDENCY)

    def build_import_journey(self, file_node_id: str) -> JourneyIR:
        cfg = JourneyConfig(
            journey_type=JourneyType.IMPORT,
            traversal_strategy=self._config.traversal_strategy,
            max_depth=self._config.max_depth,
            max_nodes=self._config.max_nodes,
            include_structural=True,  # imports are structural
            expand_strategy=self._config.expand_strategy,
            shared_subtrees=self._config.shared_subtrees,
            confidence_threshold=self._config.confidence_threshold,
        )
        ef = EdgeFilter(cfg, self._filter_config)
        exp = ExpansionFilter(cfg.expand_strategy)
        se = StopConditionEvaluator(cfg)
        ir = traverse_journey(self._query, self._g, file_node_id, cfg, ef, exp, se, self._cache)
        ir.metadata.journey_type = JourneyType.IMPORT
        return ir

    def build_data_flow_journey(self, entry_id: str) -> JourneyIR:
        return self._build_single(entry_id, JourneyType.DATA_FLOW)

    def build_repository_journey(self) -> JourneyIR:
        """Build a single-tree repository journey from all entry points.

        For forest mode, use ``build_forest()`` instead.
        """
        from md_generator.codeflow.journey.resolver import resolve_journey_starts
        starts = resolve_journey_starts(
            self._g, self._query,
            JourneyConfig(generate_all_entrypoints=True),
            [],
        )
        if not starts:
            empty = JourneyNodeIR(id="repository", label="Repository", node_type="repository", is_root=True)
            return JourneyIR(root=empty)

        # Use first entry point for single-tree mode
        return self._build_single(starts[0], JourneyType.REPOSITORY)

    def build_cross_repo_journey(self) -> JourneyIR:
        """Build a cross-repository journey (Improvement 5).

        Traverses the merged graph across repo boundaries.
        """
        from md_generator.codeflow.journey.resolver import resolve_cross_repo_starts
        # Collect repo labels from graph
        repo_labels: set[str] = set()
        for _n, d in self._g.nodes(data=True):
            rl = d.get("repository") or d.get("repo_label")
            if rl:
                repo_labels.add(str(rl))

        starts = resolve_cross_repo_starts(self._g, self._query, self._config, list(repo_labels))
        if not starts:
            empty = JourneyNodeIR(id="cross_repo", label="Cross-Repo", node_type="repository", is_root=True)
            return JourneyIR(root=empty)

        return self._build_single(starts[0], JourneyType.REPOSITORY)

    def build_business_journey(self, capability_id: str) -> JourneyIR:
        """Build a business capability journey (Improvement 11 — future stub)."""
        raise NotImplementedError(
            "Business journey requires business capability mapping — planned for future release"
        )

    # ------------------------------------------------------------------
    # Forest builder (Improvement 2)
    # ------------------------------------------------------------------

    def build_forest(self, start_ids: list[str]) -> Any:
        """Build a ``JourneyForest`` with one tree per start node.

        Returns a ``JourneyForest`` instance (from ``forest.py``).
        """
        from md_generator.codeflow.journey.forest import JourneyForest, ForestMetadata, ForestStatistics
        trees: list[JourneyIR] = []
        for sid in start_ids:
            if sid in self._g:
                ir = self._build_single(sid)
                trees.append(ir)

        # Collect repo info
        repo_labels: set[str] = set()
        entry_types: dict[str, int] = {}
        for t in trees:
            rl = t.metadata.repository
            if rl:
                repo_labels.add(rl)
            et = t.root.node_type
            entry_types[et] = entry_types.get(et, 0) + 1

        fm = ForestMetadata(
            repository=next(iter(repo_labels), None),
            branch=trees[0].metadata.branch if trees else None,
            commit=trees[0].metadata.commit if trees else None,
            tree_count=len(trees),
            entry_types=entry_types,
        )

        fs = ForestStatistics(
            tree_count=len(trees),
            total_nodes=sum(t.statistics.node_count for t in trees),
            total_edges=sum(t.statistics.edge_count for t in trees),
            max_tree_depth=max((t.statistics.maximum_depth for t in trees), default=0),
            avg_tree_depth=(
                sum(t.statistics.average_depth for t in trees) / len(trees) if trees else 0.0
            ),
            largest_tree_nodes=max((t.statistics.node_count for t in trees), default=0),
            smallest_tree_nodes=min((t.statistics.node_count for t in trees), default=0),
        )

        return JourneyForest(trees=trees, metadata=fm, statistics=fs)
