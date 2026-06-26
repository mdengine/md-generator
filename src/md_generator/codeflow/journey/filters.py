"""Journey edge, node, and stop-condition filters.

The three filter layers are evaluated in order during traversal:

    EdgeFilter.accept()  →  ExpansionFilter.should_expand()  →  StopConditionEvaluator.should_stop()

An edge must pass **all three** to be followed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_generator.codeflow.graph import relations as rel
from md_generator.codeflow.journey.models import (
    ExpansionStrategy,
    JourneyConfig,
    StopCondition,
)


# ---------------------------------------------------------------------------
# Edge types recognised by the journey system.
# Unknown types are **accepted** by default (future-proof).
# ---------------------------------------------------------------------------

_CALL_RELATIONS: frozenset[str] = frozenset({
    rel.REL_CALLS,
    rel.REL_ASYNC,
    "CALLS_ASYNC",
    "CALLS_SYNC",
})

_STRUCTURAL_RELATIONS: frozenset[str] = frozenset({
    rel.REL_IMPORTS,
    rel.REL_CROSS_REPO_IMPORT,
    rel.REL_INHERITS,
    rel.REL_IMPLEMENTS,
    rel.REL_REFERENCES,
    rel.REL_CONTAINS,
})

_EVENT_RELATIONS: frozenset[str] = frozenset({
    rel.REL_EVENT,
    "PUBLISHES_EVENT",
    "CONSUMES_EVENT",
})

# All known relations (for classification)
_ALL_KNOWN: frozenset[str] = _CALL_RELATIONS | _STRUCTURAL_RELATIONS | _EVENT_RELATIONS


# ---------------------------------------------------------------------------
# JourneyFilterConfig — fine-grained multi-dimensional filters (Improvement 7)
# ---------------------------------------------------------------------------

@dataclass
class JourneyFilterConfig:
    """Per-dimension filters for journey traversal (17 categories)."""

    languages: tuple[str, ...] = ()
    frameworks: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    classes: tuple[str, ...] = ()
    methods: tuple[str, ...] = ()
    repositories: tuple[str, ...] = ()
    branches: tuple[str, ...] = ()
    edge_types: tuple[str, ...] = ()
    min_confidence: float = 0.0
    include_async: bool = True
    include_sync: bool = True
    include_database: bool = True
    include_queue: bool = True
    include_external_api: bool = True


# ---------------------------------------------------------------------------
# EdgeFilter — decides which graph edges participate in the journey
# ---------------------------------------------------------------------------

class EdgeFilter:
    """Accept / reject edges based on ``JourneyConfig`` + ``JourneyFilterConfig``."""

    def __init__(
        self,
        config: JourneyConfig,
        filter_config: JourneyFilterConfig | None = None,
    ) -> None:
        self._config = config
        self._fc = filter_config or JourneyFilterConfig()
        # Pre-compute the set of allowed relation strings.
        self._allowed_relations = self._build_allowed()

    # ---- private ---------------------------------------------------------

    def _build_allowed(self) -> frozenset[str] | None:
        """Return ``None`` to accept all relations, or a concrete set."""
        # When specific edge types are requested, they override everything.
        if self._fc.edge_types:
            return frozenset(self._fc.edge_types)

        allowed: set[str] = set(_CALL_RELATIONS)  # CALLS always included
        if self._config.include_structural:
            allowed |= _STRUCTURAL_RELATIONS
        if self._config.include_events:
            allowed |= _EVENT_RELATIONS
        return frozenset(allowed)

    # ---- public ----------------------------------------------------------

    def accept(
        self,
        source_data: dict[str, Any],
        target_data: dict[str, Any],
        edge_data: dict[str, Any],
    ) -> bool:
        """Return ``True`` if this edge should be traversed."""
        relation = edge_data.get("relation") or edge_data.get("kind") or rel.REL_CALLS

        # 1) Relation filter
        if self._allowed_relations is not None and relation not in self._allowed_relations:
            # Unknown relations pass by default (future-proof)
            if relation in _ALL_KNOWN:
                return False

        # 2) Confidence filter
        conf = edge_data.get("confidence", 1.0)
        try:
            conf = float(conf)
        except (TypeError, ValueError):
            conf = 1.0
        if conf < self._fc.min_confidence:
            return False

        # 3) Async / sync filter
        is_async = (
            edge_data.get("async") is True
            or relation in (rel.REL_ASYNC, "CALLS_ASYNC")
        )
        if is_async and not self._fc.include_async:
            return False
        if not is_async and not self._fc.include_sync:
            return False

        # 4) Target-kind filters (database, queue, external API)
        target_type = (target_data.get("type") or target_data.get("kind") or "").lower()
        if target_type in ("table", "collection", "database") and not self._fc.include_database:
            return False
        if target_type in ("topic", "queue") and not self._fc.include_queue:
            return False
        if target_type in ("external", "external_api") and not self._fc.include_external_api:
            return False

        # 5) Multi-dimensional node filters on target
        if self._fc.languages:
            lang = (target_data.get("language") or "").lower()
            if lang and lang not in {l.lower() for l in self._fc.languages}:
                return False

        if self._fc.frameworks:
            fw = (target_data.get("framework") or "").lower()
            if fw and fw not in {f.lower() for f in self._fc.frameworks}:
                return False

        if self._fc.files:
            fp = target_data.get("file_path") or ""
            if fp and not any(f in fp for f in self._fc.files):
                return False

        if self._fc.classes:
            cn = target_data.get("class_name") or ""
            if cn and cn not in self._fc.classes:
                return False

        if self._fc.methods:
            mn = target_data.get("method_name") or target_data.get("name") or ""
            if mn and mn not in self._fc.methods:
                return False

        if self._fc.repositories:
            repo = target_data.get("repository") or target_data.get("repo_label") or ""
            if repo and repo not in self._fc.repositories:
                return False

        return True


# ---------------------------------------------------------------------------
# ExpansionFilter — controls depth into framework/library/external (Q4)
# ---------------------------------------------------------------------------

# Hierarchy levels (lower = more restrictive):
# APPLICATION=0, FRAMEWORK=1, LIBRARY=2, DATABASE=3, QUEUE=4, EXTERNAL=5, ALL=6
_EXPANSION_RANK: dict[ExpansionStrategy, int] = {
    ExpansionStrategy.APPLICATION: 0,
    ExpansionStrategy.FRAMEWORK: 1,
    ExpansionStrategy.LIBRARY: 2,
    ExpansionStrategy.DATABASE: 3,
    ExpansionStrategy.QUEUE: 4,
    ExpansionStrategy.EXTERNAL: 5,
    ExpansionStrategy.ALL: 6,
}


class ExpansionFilter:
    """Decide if a *target node* should be expanded based on ``ExpansionStrategy`` (Q4).

    Called **after** ``EdgeFilter.accept()`` and **before**
    ``StopConditionEvaluator.should_stop()``.
    """

    def __init__(self, strategy: ExpansionStrategy) -> None:
        self._strategy = strategy
        self._rank = _EXPANSION_RANK.get(strategy, 6)

    def should_expand(self, target_data: dict[str, Any]) -> bool:
        """Return ``True`` if the target should be further expanded."""
        if self._strategy is ExpansionStrategy.ALL:
            return True

        target_type = (target_data.get("type") or target_data.get("kind") or "").lower()

        # Classify the target
        is_framework = target_type == "framework" or bool(target_data.get("framework"))
        is_library = target_type == "library" or bool(target_data.get("is_library"))
        is_external = target_type in ("external", "external_api")
        is_db = target_type in ("table", "collection", "database")
        is_queue = target_type in ("topic", "queue")

        # Check if current strategy level allows this target
        if is_framework and self._rank < _EXPANSION_RANK[ExpansionStrategy.FRAMEWORK]:
            return False
        if is_library and self._rank < _EXPANSION_RANK[ExpansionStrategy.LIBRARY]:
            return False
        if is_db and self._rank < _EXPANSION_RANK[ExpansionStrategy.DATABASE]:
            return False
        if is_queue and self._rank < _EXPANSION_RANK[ExpansionStrategy.QUEUE]:
            return False
        if is_external and self._rank < _EXPANSION_RANK[ExpansionStrategy.EXTERNAL]:
            return False

        return True


# ---------------------------------------------------------------------------
# StopConditionEvaluator — check if traversal should stop at a node
# ---------------------------------------------------------------------------

class StopConditionEvaluator:
    """Evaluate the configured ``StopCondition`` set against node attributes."""

    def __init__(self, config: JourneyConfig) -> None:
        self._conditions = frozenset(config.stop_conditions)
        self._max_depth = config.effective_max_depth
        self._max_nodes = config.max_nodes
        self._confidence_threshold = config.confidence_threshold

    def should_stop(
        self,
        node_data: dict[str, Any],
        depth: int,
        path: set[str],
        *,
        node_count: int = 0,
        confidence: float = 1.0,
    ) -> StopCondition | None:
        """Return the first matching ``StopCondition``, or ``None`` to continue."""
        # System-imposed limits
        if self._max_depth is not None and depth >= self._max_depth:
            return StopCondition.MAX_DEPTH_REACHED
        if node_count >= self._max_nodes:
            return StopCondition.MAX_NODES_REACHED
        if confidence < self._confidence_threshold:
            return StopCondition.CONFIDENCE_BELOW

        if not self._conditions:
            return None

        node_type = (node_data.get("type") or node_data.get("kind") or "").lower()

        # Evaluate user-requested conditions
        if StopCondition.METHOD in self._conditions and node_type in ("method", "function", "entry"):
            return StopCondition.METHOD
        if StopCondition.CLASS in self._conditions and node_type == "class":
            return StopCondition.CLASS
        if StopCondition.PACKAGE in self._conditions and node_type == "package":
            return StopCondition.PACKAGE
        if StopCondition.MODULE in self._conditions and node_type == "module":
            return StopCondition.MODULE
        if StopCondition.REPOSITORY in self._conditions:
            repo = node_data.get("repository") or node_data.get("repo_label")
            if repo:
                return StopCondition.REPOSITORY

        if StopCondition.FRAMEWORK in self._conditions:
            if node_data.get("framework") or node_type == "framework":
                return StopCondition.FRAMEWORK
        if StopCondition.LIBRARY in self._conditions:
            if node_data.get("is_library") or node_type == "library":
                return StopCondition.LIBRARY

        if StopCondition.DATABASE in self._conditions and node_type in ("table", "collection", "database"):
            return StopCondition.DATABASE
        if StopCondition.QUEUE in self._conditions and node_type in ("topic", "queue"):
            return StopCondition.QUEUE
        if StopCondition.EXTERNAL_API in self._conditions and node_type in ("external", "external_api"):
            return StopCondition.EXTERNAL_API
        if StopCondition.RUNTIME_BOUNDARY in self._conditions:
            # Reserved — always passes for now
            pass

        return None
