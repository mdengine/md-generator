from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AbapJoin:
    table: str
    join_type: str = "INNER"
    condition: str = ""


@dataclass(slots=True)
class AbapValidation:
    rule_type: str
    expression: str
    line: int = 0


@dataclass(slots=True)
class AbapAuthCheck:
    object: str
    fields: list[str] = field(default_factory=list)
    line: int = 0


@dataclass(slots=True)
class AbapAnalysis:
    program: str
    tables: list[str] = field(default_factory=list)
    joins: list[AbapJoin] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    validations: list[AbapValidation] = field(default_factory=list)
    auth_checks: list[AbapAuthCheck] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    performs: list[str] = field(default_factory=list)
    data_declarations: list[str] = field(default_factory=list)
    types_declarations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "program": self.program,
            "tables": list(self.tables),
            "joins": [
                {"table": j.table, "join_type": j.join_type, "condition": j.condition}
                for j in self.joins
            ],
            "functions": list(self.functions),
            "validations": [
                {"rule_type": v.rule_type, "expression": v.expression, "line": v.line}
                for v in self.validations
            ],
            "auth_checks": [
                {"object": a.object, "fields": list(a.fields), "line": a.line}
                for a in self.auth_checks
            ],
            "includes": list(self.includes),
            "methods": list(self.methods),
            "performs": list(self.performs),
        }
