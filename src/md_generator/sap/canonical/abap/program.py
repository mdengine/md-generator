from __future__ import annotations

from typing import Literal

from pydantic import Field

from md_generator.sap.canonical.base import CanonicalArtifact


class AbapProgram(CanonicalArtifact):
    artifact_type: Literal["abap.program"] = "abap.program"
    tables: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    includes: list[str] = Field(default_factory=list)
