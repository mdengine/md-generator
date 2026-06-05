from __future__ import annotations

from md_generator.sap.markdown.resolved_link import (
    CONFIDENCE_BY_STRATEGY,
    ResolvedLink,
    confidence_for_strategy,
    unresolved_link,
)


def test_confidence_by_strategy_table():
    assert CONFIDENCE_BY_STRATEGY["path_registry"] == 1.0
    assert CONFIDENCE_BY_STRATEGY["same_run_name_match"] == 0.95
    assert CONFIDENCE_BY_STRATEGY["graph_walk"] == 0.85
    assert CONFIDENCE_BY_STRATEGY["heuristic_label"] == 0.55
    assert CONFIDENCE_BY_STRATEGY["unresolved"] == 0.0


def test_confidence_for_strategy_unknown():
    assert confidence_for_strategy("unknown") == 0.0


def test_resolved_link_to_dict():
    link = ResolvedLink(
        target="CHAR100",
        href="ddic/domains/char100.md",
        stable_id="DDIC::DOMAIN::CHAR100",
        confidence=1.0,
        strategy="path_registry",
        source="cross_link_registry",
        match_reason="DOMAIN:CHAR100",
    )
    d = link.to_dict()
    assert d["target"] == "CHAR100"
    assert d["confidence"] == 1.0
    assert d["strategy"] == "path_registry"


def test_unresolved_link():
    link = unresolved_link("MISSING", reason="not found")
    assert link.href is None
    assert link.confidence == 0.0
    assert link.strategy == "unresolved"
    assert link.target == "MISSING"
