from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle


class CanonicalArtifact(BaseModel):
    identity: ArtifactIdentity
    provenance: ProvenanceBundle
    artifact_type: str
    name: str
    schema: str = ""
    package: str = ""
    source_path: str = ""
    source_system: str = "sap"
    dependencies: list[str] = Field(default_factory=list)
    transformation_graph_id: str | None = None
    graph_fragment_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
