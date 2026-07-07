from __future__ import annotations

from md_generator.codeflow.journey import JourneyConfig, StopCondition, ExpansionStrategy
from md_generator.codeflow.journey.filters import (
    EdgeFilter,
    ExpansionFilter,
    StopConditionEvaluator,
    JourneyFilterConfig,
)


def test_edge_filter_basic() -> None:
    cfg = JourneyConfig()
    fc = JourneyFilterConfig()
    ef = EdgeFilter(cfg, fc)
    
    source = {}
    target = {"type": "method"}
    edge = {"relation": "CALLS", "confidence": 1.0}
    
    # 1. Basic acceptance
    assert ef.accept(source, target, edge) is True
    
    # 2. Relation filtering (structural not included by default)
    edge_struct = {"relation": "IMPORTS"}
    assert ef.accept(source, target, edge_struct) is False
    
    # Enable structural
    cfg_s = JourneyConfig(include_structural=True)
    ef_s = EdgeFilter(cfg_s, fc)
    assert ef_s.accept(source, target, edge_struct) is True


def test_edge_filter_confidence_and_async() -> None:
    cfg = JourneyConfig()
    fc = JourneyFilterConfig(min_confidence=0.8, include_async=False)
    ef = EdgeFilter(cfg, fc)
    
    source = {}
    target = {"type": "method"}
    
    # Low confidence should fail
    edge_low = {"relation": "CALLS", "confidence": 0.5}
    assert ef.accept(source, target, edge_low) is False
    
    # Async should fail
    edge_async = {"relation": "ASYNC"}
    assert ef.accept(source, target, edge_async) is False


def test_expansion_filter() -> None:
    # 1. APPLICATION strategy (default) - reject framework/library/external
    ef_app = ExpansionFilter(ExpansionStrategy.APPLICATION)
    
    assert ef_app.should_expand({"type": "method"}) is True
    assert ef_app.should_expand({"type": "framework"}) is False
    assert ef_app.should_expand({"type": "library"}) is False
    assert ef_app.should_expand({"type": "external_api"}) is False
    
    # 2. FRAMEWORK strategy - accept framework, reject library/external
    ef_fw = ExpansionFilter(ExpansionStrategy.FRAMEWORK)
    assert ef_fw.should_expand({"type": "framework"}) is True
    assert ef_fw.should_expand({"type": "library"}) is False
    
    # 3. ALL strategy - accept everything
    ef_all = ExpansionFilter(ExpansionStrategy.ALL)
    assert ef_all.should_expand({"type": "external_api"}) is True


def test_stop_condition_evaluator() -> None:
    cfg = JourneyConfig(
        max_depth=3,
        stop_conditions=(StopCondition.DATABASE, StopCondition.CLASS),
    )
    se = StopConditionEvaluator(cfg)
    
    # Max depth reached
    assert se.should_stop({}, 3, set()) == StopCondition.MAX_DEPTH_REACHED
    assert se.should_stop({}, 2, set()) is None
    
    # Stop condition database
    assert se.should_stop({"type": "table"}, 1, set()) == StopCondition.DATABASE
    assert se.should_stop({"type": "class"}, 1, set()) == StopCondition.CLASS
