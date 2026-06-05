from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResolvedLink:
    target: str
    href: str | None = None
    stable_id: str = ""
    confidence: float = 0.0
    strategy: str = "unresolved"
    source: str = ""
    match_reason: str = ""
    scores: dict[str, float] | None = None  # reserved Phase 3

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "target": self.target,
            "href": self.href,
            "stable_id": self.stable_id,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "source": self.source,
            "match_reason": self.match_reason,
        }
        if self.scores:
            d["scores"] = self.scores
        return d


CONFIDENCE_BY_STRATEGY: dict[str, float] = {
    "path_registry": 1.0,
    "same_run_name_match": 0.95,
    "same_run_kind_match": 0.90,
    "graph_walk": 0.85,
    "heuristic_label": 0.55,
    "unresolved": 0.0,
}


def confidence_for_strategy(strategy: str) -> float:
    return CONFIDENCE_BY_STRATEGY.get(strategy, 0.0)


def unresolved_link(target: str, *, reason: str = "") -> ResolvedLink:
    return ResolvedLink(
        target=target.upper(),
        href=None,
        confidence=0.0,
        strategy="unresolved",
        source="cross_link_registry",
        match_reason=reason,
    )
