from __future__ import annotations

from md_generator.codeflow.journey import (
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


def test_journey_enums() -> None:
    # Verify values and members of enums
    assert JourneyType.METHOD.value == "method"
    assert JourneyType.REPOSITORY.value == "repository"
    assert JourneyType.BUSINESS.value == "business"
    
    assert JourneySource.API_ENTRY.value == "api_entry"
    assert JourneySource.METHOD.value == "method"
    
    assert StopCondition.CYCLE_DETECTED.value == "cycle_detected"
    assert StopCondition.MAX_DEPTH_REACHED.value == "max_depth_reached"
    
    assert TraversalStrategy.DFS.value == "DFS"
    assert TraversalStrategy.BFS.value == "BFS"
    
    assert ExpansionStrategy.APPLICATION.value == "application"
    assert ExpansionStrategy.ALL.value == "all"
    
    assert SharedSubtreeMode.REFERENCE.value == "reference"
    assert SharedSubtreeMode.COLLAPSE.value == "collapse"


def test_journey_config_defaults() -> None:
    cfg = JourneyConfig()
    assert cfg.journey_type == JourneyType.METHOD
    assert cfg.traversal_strategy == TraversalStrategy.DFS
    assert cfg.max_depth == 8
    assert cfg.effective_max_depth == 8
    assert cfg.max_children == 50
    assert cfg.max_nodes == 2000
    assert cfg.expand_strategy == ExpansionStrategy.APPLICATION
    assert cfg.shared_subtrees == SharedSubtreeMode.REFERENCE
    assert cfg.include_structural is False
    assert cfg.include_events is False
    assert cfg.include_cfg is False
    assert cfg.confidence_threshold == 0.0
    assert cfg.collapse_linear_chains is True
    assert cfg.enumerate_paths is False
    assert cfg.compute_analytics is False


def test_journey_config_effective_depth() -> None:
    cfg = JourneyConfig(max_depth=0)
    assert cfg.max_depth == 0
    assert cfg.effective_max_depth is None
    
    cfg2 = JourneyConfig(max_depth=12)
    assert cfg2.max_depth == 12
    assert cfg2.effective_max_depth == 12


def test_runtime_stubs() -> None:
    prov = JourneyRuntimeProvider()
    assert prov.get_runtime_data("node_1") is None
    
    over = RuntimeOverlay()
    assert over.overlay("some_ir", prov) == "some_ir"
