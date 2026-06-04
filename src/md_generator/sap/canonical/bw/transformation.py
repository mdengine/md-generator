from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class BwTransformation(CanonicalArtifact):
    artifact_type: Literal["bw.transformation"] = "bw.transformation"
    transformation_graph: TransformationGraph | None = None
    rules: list[dict] = Field(default_factory=list)
