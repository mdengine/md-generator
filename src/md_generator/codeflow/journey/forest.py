"""JourneyForest model definitions.

Represents a multi-root collection of journey trees, mapping enterprise repositories
with multiple entry points (APIs, schedulers, events, consumer loops).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR, JourneyEdgeIR


@dataclass
class ForestMetadata:
    """Provenance and summary for a journey forest."""
    repository: str | None = None
    branch: str | None = None
    commit: str | None = None
    tree_count: int = 0
    entry_types: dict[str, int] = field(default_factory=dict)
    schema_version: str = "1.0"


@dataclass
class ForestStatistics:
    """Aggregated statistics across all trees in the forest."""
    tree_count: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    max_tree_depth: int = 0
    avg_tree_depth: float = 0.0
    largest_tree_nodes: int = 0
    smallest_tree_nodes: int = 0


@dataclass
class JourneyForest:
    """A collection of distinct JourneyIR trees from multiple entry points."""
    trees: list[JourneyIR] = field(default_factory=list)
    metadata: ForestMetadata = field(default_factory=ForestMetadata)
    statistics: ForestStatistics = field(default_factory=ForestStatistics)
    cross_tree_edges: list[JourneyEdgeIR] = field(default_factory=list)
