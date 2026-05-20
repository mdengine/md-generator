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
                    "key": f.key,
                    "domain": f.domain,
                    "check_table": f.check_table,
                    "business_name": f.business_name,
                }
                for f in self.fields
            ],
        }
