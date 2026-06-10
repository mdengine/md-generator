from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DdicField:
    name: str
    data_type: str = ""
    length: int = 0
    key: bool = False
    domain: str = ""
    data_element: str = ""
    check_table: str = ""
    business_name: str = ""


@dataclass(slots=True)
class DdicTable:
    name: str
    description: str = ""
    fields: list[DdicField] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    package: str = ""
    table_type: str = ""
    annotations: dict[str, str] = field(default_factory=dict)
    definition_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "primary_key": list(self.primary_key),
            "package": self.package,
            "table_type": self.table_type,
            "annotations": dict(self.annotations),
            "definition_source": self.definition_source,
            "fields": [
                {
                    "name": f.name,
                    "data_type": f.data_type,
                    "length": f.length,
                    "key": f.key,
                    "domain": f.domain,
                    "data_element": f.data_element,
                    "check_table": f.check_table,
                    "business_name": f.business_name,
                }
                for f in self.fields
            ],
        }


@dataclass(slots=True)
class DdicDataElement:
    name: str
    description: str = ""
    package: str = ""
    type_kind: str = ""
    type_name: str = ""
    data_type: str = ""
    data_type_length: int = 0
    data_type_decimals: int = 0
    short_field_label: str = ""
    medium_field_label: str = ""
    long_field_label: str = ""
    heading_field_label: str = ""
    search_help: str = ""
    change_document: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "type_kind": self.type_kind,
            "type_name": self.type_name,
            "data_type": self.data_type,
            "data_type_length": self.data_type_length,
            "data_type_decimals": self.data_type_decimals,
            "short_field_label": self.short_field_label,
            "medium_field_label": self.medium_field_label,
            "long_field_label": self.long_field_label,
            "heading_field_label": self.heading_field_label,
            "search_help": self.search_help,
            "change_document": self.change_document,
        }


@dataclass(slots=True)
class DdicDomain:
    name: str
    description: str = ""
    package: str = ""
    data_type: str = ""
    length: int = 0
    decimals: int = 0
    output_length: int = 0
    value_table: str = ""
    conversion_routine: str = ""
    lower_case: bool = False
    sign_flag: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "data_type": self.data_type,
            "length": self.length,
            "decimals": self.decimals,
            "output_length": self.output_length,
            "value_table": self.value_table,
            "conversion_routine": self.conversion_routine,
            "lower_case": self.lower_case,
            "sign_flag": self.sign_flag,
        }


@dataclass(slots=True)
class DdicComponent:
    name: str
    data_element: str = ""
    data_type: str = ""
    type_name: str = ""
    type_kind: str = ""
    length: int = 0
    include_structure: str = ""
    component_type: str = ""
    children: list["DdicComponent"] = field(default_factory=list)
    cycle_detected: bool = False
    cycle_path: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "data_element": self.data_element,
            "data_type": self.data_type,
            "type_name": self.type_name,
            "type_kind": self.type_kind,
            "length": self.length,
        }
        if self.include_structure:
            d["include_structure"] = self.include_structure
        if self.component_type:
            d["component_type"] = self.component_type
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        if self.cycle_detected:
            d["cycle_detected"] = True
            d["cycle_path"] = list(self.cycle_path)
        return d


@dataclass(slots=True)
class DdicStructure:
    name: str
    description: str = ""
    package: str = ""
    components: list[DdicComponent] = field(default_factory=list)
    definition_source: str = "adt_xml"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "components": [c.to_dict() for c in self.components],
            "definition_source": self.definition_source,
        }


@dataclass(slots=True)
class DdicTableType:
    name: str
    description: str = ""
    package: str = ""
    row_type: str = ""
    line_type: str = ""
    access_mode: str = ""
    primary_key: list[str] = field(default_factory=list)
    definition_source: str = "adt_xml"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "row_type": self.row_type,
            "line_type": self.line_type,
            "access_mode": self.access_mode,
            "primary_key": list(self.primary_key),
            "definition_source": self.definition_source,
        }


@dataclass(slots=True)
class DdicRangeType:
    name: str
    description: str = ""
    package: str = ""
    data_element: str = ""
    domain: str = ""
    length: int = 0
    decimals: int = 0
    definition_source: str = "adt_xml"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "data_element": self.data_element,
            "domain": self.domain,
            "length": self.length,
            "decimals": self.decimals,
            "definition_source": self.definition_source,
        }


@dataclass(slots=True)
class DdicReferenceType:
    name: str
    description: str = ""
    package: str = ""
    referenced_type: str = ""
    check_table: str = ""
    definition_source: str = "adt_xml"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "referenced_type": self.referenced_type,
            "check_table": self.check_table,
            "definition_source": self.definition_source,
        }
