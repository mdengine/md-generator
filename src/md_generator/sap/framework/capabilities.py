from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ParserCapability(BaseModel):
    lineage: bool = False
    sql_generation: Literal["yes", "partial", "no"] = "no"
    impact_analysis: bool = False
    semantic_id: bool = False
    transformation_graph: bool = False


def default_capabilities() -> ParserCapability:
    return ParserCapability()
