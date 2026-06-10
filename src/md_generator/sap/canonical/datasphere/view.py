from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class DatasphereView(CanonicalArtifact):
    artifact_type: Literal["datasphere.view"] = "datasphere.view"
    transformation_graph: TransformationGraph | None = None
    columns: list[str] = Field(default_factory=list)
