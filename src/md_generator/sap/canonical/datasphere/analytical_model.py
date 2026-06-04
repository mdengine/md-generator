from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class DatasphereAnalyticalModel(CanonicalArtifact):
    artifact_type: Literal["datasphere.analytical_model"] = "datasphere.analytical_model"
    transformation_graph: TransformationGraph | None = None
    measures: list[str] = Field(default_factory=list)
