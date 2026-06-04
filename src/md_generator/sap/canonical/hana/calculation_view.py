from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


class DataSource(BaseModel):
    name: str
    schema: str = ""
    object_type: str = "table"


class CalculatedColumn(BaseModel):
    name: str
    expression: str = ""
    data_type: str = ""


class Variable(BaseModel):
    name: str
    default_value: str = ""


class InputParameter(BaseModel):
    name: str
    data_type: str = ""


class Measure(BaseModel):
    name: str
    aggregation: str = ""


class Attribute(BaseModel):
    name: str
    data_type: str = ""


class CalculationView(CanonicalArtifact):
    artifact_type: Literal["hana.calculation_view"] = "hana.calculation_view"
    data_sources: list[DataSource] = Field(default_factory=list)
    transformation_graph: TransformationGraph | None = None
    calculated_columns: list[CalculatedColumn] = Field(default_factory=list)
    variables: list[Variable] = Field(default_factory=list)
    input_parameters: list[InputParameter] = Field(default_factory=list)
    measures: list[Measure] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    semantics: dict[str, str] = Field(default_factory=dict)

    def to_metadata_dict(self) -> dict[str, Any]:
        base = self.model_dump(mode="json")
        meta = {
            "data_sources": [ds.model_dump(mode="json") for ds in self.data_sources],
            "transformation_graph": self.transformation_graph.model_dump(mode="json")
            if self.transformation_graph
            else None,
            "calculated_columns": [c.model_dump(mode="json") for c in self.calculated_columns],
            "variables": [v.model_dump(mode="json") for v in self.variables],
            "measures": [m.model_dump(mode="json") for m in self.measures],
            "attributes": [a.model_dump(mode="json") for a in self.attributes],
            "semantics": self.semantics,
        }
        base["metadata"] = meta
        return base
