from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

StatementKind = Literal["select", "insert", "update", "delete", "modify", "other"]
SourceType = Literal["OPEN_SQL", "EXEC_SQL", "ADBC", "DYNAMIC_SQL"]
ViewKind = Literal[
    "ddic_table",
    "cds",
    "hana_calc",
    "hana_analytic",
    "hana_attribute",
    "hana_sql",
    "hdi",
    "unknown",
]
LineageCompleteness = Literal["complete", "partial", "unknown"]


@dataclass(slots=True)
class SqlAstNode:
    """Lightweight structural AST; populated by regex today, parser-ready for Phase 2."""

    node_kind: str
    value: str = ""
    children: list[SqlAstNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_kind": self.node_kind,
            "value": self.value,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass(slots=True)
class ResolutionResult:
    target: str
    resolved_stable_id: str = ""
    resolved_path: str = ""
    confidence: float = 0.0
    resolution_strategy: str = "unresolved"
    match_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "resolved_stable_id": self.resolved_stable_id,
            "resolved_path": self.resolved_path,
            "confidence": self.confidence,
            "resolution_strategy": self.resolution_strategy,
            "match_reason": self.match_reason,
        }


@dataclass(slots=True)
class SqlComplexity:
    join_count: int = 0
    subquery_count: int = 0
    complexity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "join_count": self.join_count,
            "subquery_count": self.subquery_count,
            "complexity_score": self.complexity_score,
        }


@dataclass(slots=True)
class DynamicSqlSignal:
    pattern: str
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"pattern": self.pattern, "line": self.line}


@dataclass(slots=True)
class AbapJoin:
    table: str
    join_type: str = "INNER"
    condition: str = ""
    left_table: str = ""
    right_table: str = ""
    line: int = 0


@dataclass(slots=True)
class AbapSqlStatement:
    statement_kind: StatementKind
    source_type: SourceType
    text: str
    line: int = 0
    objects: list[str] = field(default_factory=list)
    where_clause: str = ""
    fingerprint: str = ""
    stable_id: str = ""
    confidence: float = 1.0
    dynamic_sql_risk: bool = False
    lineage_completeness: LineageCompleteness = "complete"
    complexity: SqlComplexity = field(default_factory=SqlComplexity)
    ast_root: SqlAstNode | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement_kind": self.statement_kind,
            "source_type": self.source_type,
            "text": self.text,
            "line": self.line,
            "objects": list(self.objects),
            "where_clause": self.where_clause,
            "fingerprint": self.fingerprint,
            "stable_id": self.stable_id,
            "confidence": self.confidence,
            "dynamic_sql_risk": self.dynamic_sql_risk,
            "lineage_completeness": self.lineage_completeness,
            "complexity": self.complexity.to_dict(),
            "ast_root": self.ast_root.to_dict() if self.ast_root else None,
        }


@dataclass(slots=True)
class AbapViewReference:
    name: str
    schema: str = ""
    kind: ViewKind = "unknown"
    confidence: float = 0.5
    source_sql_line: int = 0
    resolution: ResolutionResult = field(default_factory=lambda: ResolutionResult(target=""))

    def to_dict(self) -> dict[str, Any]:
        res = self.resolution
        if not res.target:
            res = ResolutionResult(target=self.name, resolution_strategy="heuristic_only")
        return {
            "name": self.name,
            "schema": self.schema,
            "kind": self.kind,
            "confidence": self.confidence,
            "source_sql_line": self.source_sql_line,
            "resolved_stable_id": res.resolved_stable_id,
            "resolved_path": res.resolved_path,
            "resolution": res.to_dict(),
        }


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
    sql_statements: list[AbapSqlStatement] = field(default_factory=list)
    view_references: list[AbapViewReference] = field(default_factory=list)
    dynamic_sql_signals: list[DynamicSqlSignal] = field(default_factory=list)
    lineage_completeness: LineageCompleteness = "complete"
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
                {
                    "table": j.table,
                    "join_type": j.join_type,
                    "condition": j.condition,
                    "left_table": j.left_table,
                    "right_table": j.right_table,
                    "line": j.line,
                }
                for j in self.joins
            ],
            "sql_statements": [s.to_dict() for s in self.sql_statements],
            "view_references": [v.to_dict() for v in self.view_references],
            "dynamic_sql_signals": [d.to_dict() for d in self.dynamic_sql_signals],
            "lineage_completeness": self.lineage_completeness,
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
