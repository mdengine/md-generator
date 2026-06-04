from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class DatasphereDataFlow(CanonicalArtifact):
    artifact_type: Literal["datasphere.data_flow"] = "datasphere.data_flow"
    transformation_graph: TransformationGraph | None = None
    steps: list[dict] = Field(default_factory=list)
