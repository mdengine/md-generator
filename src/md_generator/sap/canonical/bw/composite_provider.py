from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class BwCompositeProvider(CanonicalArtifact):
    artifact_type: Literal["bw.composite_provider"] = "bw.composite_provider"
    transformation_graph: TransformationGraph | None = None
    members: list[str] = Field(default_factory=list)
