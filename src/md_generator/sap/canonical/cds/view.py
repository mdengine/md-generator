from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class CdsView(CanonicalArtifact):
    artifact_type: Literal["cds.view"] = "cds.view"
    sql_view_name: str = ""
    base_tables: list[str] = Field(default_factory=list)
    associations: list[dict] = Field(default_factory=list)
    transformation_graph: TransformationGraph | None = None
