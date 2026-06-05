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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "primary_key": list(self.primary_key),
            "package": self.package,
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
