from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticMatch(BaseModel):
    confidence_score: float = Field(ge=0.0, le=1.0)
    matching_strategy: str
    match_reason: str = ""

    def to_edge_properties(self) -> dict:
        return {
            "semantic_match": self.model_dump(mode="json"),
            "confidence_score": self.confidence_score,
            "matching_strategy": self.matching_strategy,
            "match_reason": self.match_reason,
        }
