from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from md_generator.sap.canonical.base import CanonicalArtifact


class DdicField(BaseModel):
    name: str
    type: str = ""
    check_table: str = ""


class DdicTable(CanonicalArtifact):
    artifact_type: Literal["ddic.table"] = "ddic.table"
    fields: list[DdicField] = Field(default_factory=list)
    delivery_class: str = ""
