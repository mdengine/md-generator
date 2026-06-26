"""Journey Generator package initialization.

Exports the primary config enums, models, IR containers, builders,
forest structures, paths utilities, and diff calculators.
"""

from __future__ import annotations

from md_generator.codeflow.journey.models import (
    JourneyConfig,
    JourneyType,
    JourneySource,
    StopCondition,
    TraversalStrategy,
    ExpansionStrategy,
    SharedSubtreeMode,
    JourneyRuntimeProvider,
    RuntimeOverlay,
)
from md_generator.codeflow.journey.ir import (
    JourneyIR,
    JourneyNodeIR,
    JourneyEdgeIR,
    JourneyMetadata,
    CfgOverlay,
)
from md_generator.codeflow.journey.builder import JourneyBuilder
from md_generator.codeflow.journey.forest import JourneyForest
from md_generator.codeflow.journey.statistics import JourneyStatistics, compute_statistics
from md_generator.codeflow.journey.analyzer import JourneyAnalyzer, JourneyAnalysis
from md_generator.codeflow.journey.paths import ExecutionPath, enumerate_execution_paths
from md_generator.codeflow.journey.diff import JourneyDiff, compute_journey_diff

__all__ = [
    "JourneyConfig",
    "JourneyType",
    "JourneySource",
    "StopCondition",
    "TraversalStrategy",
    "ExpansionStrategy",
    "SharedSubtreeMode",
    "JourneyRuntimeProvider",
    "RuntimeOverlay",
    "JourneyIR",
    "JourneyNodeIR",
    "JourneyEdgeIR",
    "JourneyMetadata",
    "CfgOverlay",
    "JourneyBuilder",
    "JourneyForest",
    "JourneyStatistics",
    "compute_statistics",
    "JourneyAnalyzer",
    "JourneyAnalysis",
    "ExecutionPath",
    "enumerate_execution_paths",
    "JourneyDiff",
    "compute_journey_diff",
]
