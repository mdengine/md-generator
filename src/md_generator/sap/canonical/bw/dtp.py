from __future__ import annotations

from typing import Literal

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class BwDtp(CanonicalArtifact):
    artifact_type: Literal["bw.dtp"] = "bw.dtp"
    transformation_graph: TransformationGraph | None = None
    source_name: str = ""
    target_name: str = ""
