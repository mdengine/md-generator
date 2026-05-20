from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CdsAssociation:
    name: str
    target: str
    cardinality: str = ""
    kind: str = "association"


@dataclass(slots=True)
class CdsAnalysis:
    view_name: str
    entities: list[str] = field(default_factory=list)
    joins: list[str] = field(default_factory=list)
    associations: list[CdsAssociation] = field(default_factory=list)
    annotations: dict[str, str] = field(default_factory=dict)
    semantic_tags: list[str] = field(default_factory=list)
    compositions: list[str] = field(default_factory=list)
    projections: list[str] = field(default_factory=list)
    semantic_entity: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_name": self.view_name,
            "entities": list(self.entities),
            "joins": list(self.joins),
            "associations": [
                {
                    "name": a.name,
                    "target": a.target,
                    "cardinality": a.cardinality,
                    "kind": a.kind,
                }
                for a in self.associations
            ],
            "annotations": dict(self.annotations),
            "semantic_tags": list(self.semantic_tags),
            "compositions": list(self.compositions),
            "projections": list(self.projections),
            "semantic_entity": self.semantic_entity,
        }
