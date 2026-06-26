"""Journey Generator configuration enums and dataclass models.

This module defines all enum types and the ``JourneyConfig`` dataclass used to
drive the Journey Generator pipeline.  It deliberately contains **no** tree /
node data structures — those live in ``ir.py`` to keep the builder↔exporter
separation clean.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Journey Type — what kind of journey to build
# ---------------------------------------------------------------------------

class JourneyType(str, Enum):
    """All supported journey kinds (16 active + 3 future)."""

    REPOSITORY = "repository"
    PROJECT = "project"
    MODULE = "module"
    PACKAGE = "package"
    FOLDER = "folder"
    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    API = "api"
    DATABASE = "database"
    QUEUE = "queue"
    CONFIG = "config"
    DEPENDENCY = "dependency"
    EVENT = "event"
    IMPORT = "import"
    DATA_FLOW = "data_flow"
    # Future placeholders
    BUSINESS = "business"
    SECURITY = "security"
    RUNTIME = "runtime"


# ---------------------------------------------------------------------------
# Journey Source — valid starting points for a journey
# ---------------------------------------------------------------------------

class JourneySource(str, Enum):
    """What a journey can originate from."""

    REPOSITORY = "repository"
    WORKSPACE = "workspace"
    PROJECT = "project"
    MODULE = "module"
    PACKAGE = "package"
    FOLDER = "folder"
    FILE = "file"
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    METHOD = "method"
    FUNCTION = "function"
    API_ENTRY = "api_entry"
    SCHEDULER = "scheduler"
    QUEUE_CONSUMER = "queue_consumer"
    EVENT_LISTENER = "event_listener"
    CLI_ENTRY = "cli_entry"
    MAIN_FUNCTION = "main_function"
    # Future
    RUNTIME_TRACE = "runtime_trace"


# ---------------------------------------------------------------------------
# Stop Condition — when to stop expanding a branch
# ---------------------------------------------------------------------------

class StopCondition(str, Enum):
    """Reasons for halting traversal at a node."""

    METHOD = "method"
    CLASS = "class"
    PACKAGE = "package"
    MODULE = "module"
    REPOSITORY = "repository"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    DATABASE = "database"
    QUEUE = "queue"
    EXTERNAL_API = "external_api"
    RUNTIME_BOUNDARY = "runtime_boundary"
    # Automatic / system-imposed
    CYCLE_DETECTED = "cycle_detected"
    MAX_DEPTH_REACHED = "max_depth_reached"
    MAX_NODES_REACHED = "max_nodes_reached"
    LEAF_NODE = "leaf_node"
    CONFIDENCE_BELOW = "confidence_below"


# ---------------------------------------------------------------------------
# Traversal Strategy — DFS vs BFS
# ---------------------------------------------------------------------------

class TraversalStrategy(str, Enum):
    DFS = "DFS"
    BFS = "BFS"


# ---------------------------------------------------------------------------
# Expansion Strategy — controls what gets expanded (Q4)
# ---------------------------------------------------------------------------

class ExpansionStrategy(str, Enum):
    """Controls *what* the traversal expands into.

    ``APPLICATION`` (default) expands only application code — stops at
    framework / library / external / DB / queue boundaries.  Each successive
    level opens one more boundary.  ``ALL`` expands everything.
    """

    APPLICATION = "application"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    DATABASE = "database"
    QUEUE = "queue"
    EXTERNAL = "external"
    ALL = "all"


# ---------------------------------------------------------------------------
# Shared Subtree Mode — duplicate subtree handling (Q5)
# ---------------------------------------------------------------------------

class SharedSubtreeMode(str, Enum):
    """How to handle a method that appears in multiple branches.

    ``REFERENCE`` (default) renders the first occurrence fully and subsequent
    occurrences as a lightweight reference node.
    """

    REFERENCE = "reference"
    DUPLICATE = "duplicate"
    COLLAPSE = "collapse"


# ---------------------------------------------------------------------------
# Journey Config — central configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class JourneyConfig:
    """Full configuration for a single journey generation run.

    Defaults are chosen for typical enterprise repositories.
    ``max_depth=0`` means unlimited (Q1) — still bounded by ``max_nodes``,
    cycle detection, and stop conditions.
    """

    journey_type: JourneyType = JourneyType.METHOD
    traversal_strategy: TraversalStrategy = TraversalStrategy.DFS
    max_depth: int = 8
    max_children: int = 50
    max_nodes: int = 2000
    stop_conditions: tuple[StopCondition, ...] = ()
    expand_strategy: ExpansionStrategy = ExpansionStrategy.APPLICATION
    shared_subtrees: SharedSubtreeMode = SharedSubtreeMode.REFERENCE
    include_structural: bool = False
    include_events: bool = False
    include_framework: bool = False
    include_library: bool = False
    include_cfg: bool = False
    confidence_threshold: float = 0.0
    collapse_linear_chains: bool = True
    enumerate_paths: bool = False
    compute_analytics: bool = False
    build_forest: bool = False
    cross_repo: bool = False
    output_formats: tuple[str, ...] = ("md", "json", "mermaid")
    generate_all_files: bool = False
    generate_all_classes: bool = False
    generate_all_methods: bool = False
    generate_all_entrypoints: bool = False
    generate_diff: bool = False
    schema_version: str = "1.0"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def effective_max_depth(self) -> int | None:
        """Return ``None`` when depth is unlimited (0), else the configured value."""
        return None if self.max_depth == 0 else self.max_depth


# ---------------------------------------------------------------------------
# Runtime extension stubs — future only
# ---------------------------------------------------------------------------

class JourneyRuntimeProvider:
    """Future: provides runtime trace data to overlay on journey trees.

    Sub-classes will implement ``get_runtime_data`` to return timing, counts
    etc. for a given graph node.  The current implementation is a no-op stub.
    """

    def get_runtime_data(self, node_id: str) -> dict[str, Any] | None:  # pragma: no cover
        return None


class RuntimeOverlay:
    """Future: merges runtime trace data into an existing JourneyIR."""

    def overlay(self, ir: Any, provider: JourneyRuntimeProvider) -> Any:  # pragma: no cover
        return ir
