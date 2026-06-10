from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class BwInfoObject(CanonicalArtifact):
    artifact_type: Literal["bw.info_object"] = "bw.info_object"
    transformation_graph: TransformationGraph | None = None
    characteristics: list[str] = Field(default_factory=list)
    key_figures: list[str] = Field(default_factory=list)
