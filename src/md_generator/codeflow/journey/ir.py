"""Journey Intermediate Representation (JourneyIR).

The **central internal model** produced by the builder and consumed by every
exporter (markdown, mermaid, html, json, graph).  This layer cleanly separates
builder internals from the export contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_generator.codeflow.journey.models import JourneyConfig, JourneyType, StopCondition


# ---------------------------------------------------------------------------
# CFG Overlay — inline control-flow info on a journey node
# ---------------------------------------------------------------------------

@dataclass
class CfgOverlay:
    """Control-flow fragment rendered inline within a journey node.

    ``kind`` values: IF, ELSE, ELIF, SWITCH, CASE, FOR, WHILE, DO_WHILE,
    BREAK, CONTINUE, RETURN, TRY, CATCH, FINALLY, THROW, ASYNC, AWAIT,
    FUTURE, CALLBACK.
    """

    kind: str
    condition: str | None = None
    label: str | None = None
    children: list[CfgOverlay] = field(default_factory=list)


# ---------------------------------------------------------------------------
# JourneyEdgeIR — flat edge record for graph exports
# ---------------------------------------------------------------------------

@dataclass
class JourneyEdgeIR:
    """One directed edge between two journey nodes."""

    source_id: str
    target_id: str
    relation: str
    label: str | None = None
    call_type: str | None = None
    confidence: float = 1.0
    is_async: bool = False
    is_cycle_edge: bool = False
    annotations: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# JourneyNodeIR — rich tree node
# ---------------------------------------------------------------------------

@dataclass
class JourneyNodeIR:
    """One node in the journey tree with full metadata.

    The ``children`` list forms the tree structure.  Each child is itself a
    ``JourneyNodeIR`` instance.

    Enhanced metadata fields (Improvement 4):
    * ``execution_order`` — global DFS/BFS visit index
    * ``branch_id`` — hierarchical address e.g. ``"0.1.2"``
    * ``path_id`` — execution-path this node belongs to (populated by paths.py)
    * ``parent_id`` — graph node ID of the parent (``None`` for root)
    * ``sibling_index`` — 0-based position among siblings
    * ``is_leaf`` / ``is_root`` / ``is_collapsed`` / ``is_virtual`` /
      ``is_generated`` / ``is_synthetic`` — rendering hints
    """

    # Identity
    id: str
    label: str
    node_type: str  # method | class | file | entry | external | topic | table | queue | config

    # Source location
    language: str | None = None
    file_path: str | None = None
    class_name: str | None = None
    method_name: str | None = None
    framework: str | None = None
    line: int | None = None

    # Edge from parent → this node
    edge_relation: str | None = None
    edge_label: str | None = None
    call_type: str | None = None  # sync | async | unknown
    confidence: float = 1.0

    # Stop / cycle info
    stop_reason: StopCondition | None = None
    is_cycle: bool = False
    is_recursive: bool = False

    # Enhanced metadata (Improvement 4)
    depth: int = 0
    execution_order: int = 0
    traversal_index: int = 0
    branch_id: str = "0"
    path_id: str | None = None
    parent_id: str | None = None
    sibling_index: int = 0
    is_leaf: bool = True
    is_root: bool = False
    is_collapsed: bool = False
    is_virtual: bool = False
    is_generated: bool = False
    is_synthetic: bool = False

    # Optional overlays
    annotations: dict[str, Any] = field(default_factory=dict)
    cfg_info: CfgOverlay | None = None

    # Children
    children: list[JourneyNodeIR] = field(default_factory=list)


# ---------------------------------------------------------------------------
# JourneyMetadata — header / provenance for a single journey
# ---------------------------------------------------------------------------

@dataclass
class JourneyMetadata:
    """Provenance and summary info attached to every ``JourneyIR``."""

    journey_type: JourneyType = JourneyType.METHOD
    entry_id: str = ""
    entry_label: str = ""
    repository: str | None = None
    branch: str | None = None
    commit: str | None = None
    config: JourneyConfig = field(default_factory=JourneyConfig)
    schema_version: str = "1.0"
    timestamp: str = ""
    total_nodes: int = 0
    total_depth: int = 0
    truncated: bool = False
    cycle_nodes: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# JourneyStatistics (declared here, computed in statistics.py)
# ---------------------------------------------------------------------------
# Forward-imported into this module to keep the JourneyIR dataclass complete.

@dataclass
class JourneyStatistics:
    """Metrics computed from a ``JourneyIR`` tree."""

    maximum_depth: int = 0
    average_depth: float = 0.0
    leaf_count: int = 0
    branch_count: int = 0
    node_count: int = 0
    edge_count: int = 0
    recursion_count: int = 0
    cycle_count: int = 0
    external_api_count: int = 0
    database_count: int = 0
    queue_count: int = 0
    configuration_count: int = 0
    framework_count: int = 0
    execution_path_count: int = 0
    language_distribution: dict[str, int] = field(default_factory=dict)
    node_type_distribution: dict[str, int] = field(default_factory=dict)
    edge_type_distribution: dict[str, int] = field(default_factory=dict)
    stop_reason_distribution: dict[str, int] = field(default_factory=dict)
    truncation_count: int = 0


# ---------------------------------------------------------------------------
# JourneyIR — the complete intermediate representation
# ---------------------------------------------------------------------------

@dataclass
class JourneyIR:
    """Complete intermediate representation for one journey.

    Builder produces this; all exporters consume this.
    """

    root: JourneyNodeIR
    metadata: JourneyMetadata = field(default_factory=JourneyMetadata)
    statistics: JourneyStatistics = field(default_factory=JourneyStatistics)
    edges: list[JourneyEdgeIR] = field(default_factory=list)
    # Populated by paths.py when ``enumerate_paths`` is enabled.
    execution_paths: list[Any] | None = None  # list[ExecutionPath] — avoid circular import
