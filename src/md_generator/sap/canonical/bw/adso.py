from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class BwAdso(CanonicalArtifact):
    artifact_type: Literal["bw.adso"] = "bw.adso"
    transformation_graph: TransformationGraph | None = None
    fields: list[str] = Field(default_factory=list)
