from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, Field

from md_generator.sap.models.metadata.ddic_kinds import DdicObjectKind


class DataElementMetadata(BaseModel):
    kind: Literal["DATA_ELEMENT"] = "DATA_ELEMENT"
    type_kind: str = ""
    type_name: str = ""
    data_type: str = ""
    data_type_length: int = 0
    data_type_decimals: int = 0


class DomainMetadata(BaseModel):
    kind: Literal["DOMAIN"] = "DOMAIN"
    data_type: str = ""
    length: int = 0
    decimals: int = 0
    value_table: str = ""


class StructureComponentMetadata(BaseModel):
    name: str
    data_element: str = ""
    type_kind: str = ""
    type_name: str = ""
    data_type: str = ""
    length: int = 0
    children: list["StructureComponentMetadata"] = Field(default_factory=list)
    cycle_detected: bool = False
    cycle_path: list[str] = Field(default_factory=list)


class StructureMetadata(BaseModel):
    kind: Literal["STRUCTURE"] = "STRUCTURE"
    definition_source: str = "adt_xml"
    components: list[StructureComponentMetadata] = Field(default_factory=list)


class TableFieldMetadata(BaseModel):
    name: str
    data_element: str = ""
    data_type: str = ""
    length: int = 0
    key: bool = False


class TableMetadata(BaseModel):
    kind: Literal["TABLE"] = "TABLE"
    definition_source: str = ""
    table_type: str = ""
    fields: list[TableFieldMetadata] = Field(default_factory=list)


class TableTypeMetadata(BaseModel):
    kind: Literal["TABLE_TYPE"] = "TABLE_TYPE"
    row_type: str = ""
    line_type: str = ""
    access_mode: str = ""


class RangeTypeMetadata(BaseModel):
    kind: Literal["RANGE_TYPE"] = "RANGE_TYPE"
    data_element: str = ""
    domain: str = ""


class ReferenceTypeMetadata(BaseModel):
    kind: Literal["REFERENCE_TYPE"] = "REFERENCE_TYPE"
    referenced_type: str = ""
    check_table: str = ""


DdicCanonicalPayload = Union[
    DataElementMetadata,
    DomainMetadata,
    StructureMetadata,
    TableMetadata,
    TableTypeMetadata,
    RangeTypeMetadata,
    ReferenceTypeMetadata,
]


class DdicCanonicalMetadata(BaseModel):
    object_kind: DdicObjectKind
    definition_source: str = "adt_xml"
    payload: DdicCanonicalPayload | dict = Field(default_factory=dict)


StructureComponentMetadata.model_rebuild()
