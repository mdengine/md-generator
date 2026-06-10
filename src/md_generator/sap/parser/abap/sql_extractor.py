from __future__ import annotations

import re

from md_generator.sap.models.metadata.abap import (
    AbapJoin,
    AbapSqlStatement,
    SqlAstNode,
    SqlComplexity,
    StatementKind,
)
from md_generator.sap.parser.abap.sql_fingerprint import sql_fingerprint

_MAX_SQL_LEN = 2048

_RE_SELECT_FROM = re.compile(
    r"\bFROM\s+(?:TABLE\s+)?(?:([\w/]+)(?:\s+AS\s+(\w+))?|\"([^\"]+)\"\s*\.\s*\"([^\"]+)\")",
    re.I,
)
_RE_JOIN = re.compile(
    r"\b((?:INNER|LEFT(?:\s+OUTER)?|RIGHT(?:\s+OUTER)?|FULL(?:\s+OUTER)?)?\s*JOIN)\s+"
    r"(?:([\w/]+)(?:\s+AS\s+(\w+))?|\"([^\"]+)\"\s*\.\s*\"([^\"]+)\")"
    r"(?:\s+ON\s+(.+?))?(?=\s+(?:INNER|LEFT|RIGHT|FULL|WHERE|GROUP|ORDER|INTO|HAVING|$))",
    re.I,
)
_RE_WHERE = re.compile(r"\bWHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s+INTO|\s+HAVING|$)", re.I)
_RE_TABLE_OPS = re.compile(
    r"\b(UPDATE|MODIFY|DELETE\s+FROM|INSERT\s+INTO)\s+(?:TABLE\s+)?([\w/]+|\"([^\"]+)\"\s*\.\s*\"([^\"]+)\")",
    re.I,
)
_RE_SUBQUERY = re.compile(r"\(\s*SELECT\b", re.I)


def _normalize_text(text: str) -> str:
    s = re.sub(r"\s+", " ", text.strip())
    return s[:_MAX_SQL_LEN]


def _object_token(*groups: str | None) -> str:
    if groups[2] and groups[3]:
        return f'"{groups[2]}"."{groups[3]}"'
    if groups[0]:
        return groups[0].upper()
    return ""


def _statement_kind(upper: str) -> StatementKind:
    if upper.startswith("SELECT"):
        return "select"
    if upper.startswith("INSERT"):
        return "insert"
    if upper.startswith("UPDATE"):
        return "update"
    if upper.startswith("DELETE"):
        return "delete"
    if upper.startswith("MODIFY"):
        return "modify"
    return "other"


def _compute_complexity(text: str, join_count: int) -> SqlComplexity:
    subquery_count = len(_RE_SUBQUERY.findall(text))
    score = min(10.0, join_count * 1.5 + subquery_count * 2.0 + (1.0 if " UNION " in text.upper() else 0))
    return SqlComplexity(join_count=join_count, subquery_count=subquery_count, complexity_score=round(score, 2))


def _build_ast(text: str, objects: list[str], where: str, joins: list[AbapJoin]) -> SqlAstNode:
    children: list[SqlAstNode] = []
    if objects:
        from_node = SqlAstNode(node_kind="from", children=[SqlAstNode(node_kind="object_ref", value=o) for o in objects])
        children.append(from_node)
    for j in joins:
        children.append(
            SqlAstNode(
                node_kind="join",
                value=j.join_type,
                children=[
                    SqlAstNode(node_kind="object_ref", value=j.right_table or j.table),
                    SqlAstNode(node_kind="on", value=j.condition),
                ],
            )
        )
    if where:
        children.append(SqlAstNode(node_kind="where", value=where))
    return SqlAstNode(node_kind="select", value=text[:120], children=children)


def extract_open_sql_statements(
    statements: list[tuple[int, str]],
    program: str,
) -> tuple[list[AbapSqlStatement], list[AbapJoin], set[str]]:
    """Extract Open SQL statements, joins, and table names from ABAP statements."""
    sql_stmts: list[AbapSqlStatement] = []
    joins: list[AbapJoin] = []
    tables: set[str] = set()
    seen_fp: set[str] = set()

    for line_no, stmt in statements:
        upper = stmt.upper()
        kind = _statement_kind(upper)
        is_sql = kind in ("select", "insert", "update", "delete", "modify")
        if not is_sql:
            continue

        text = _normalize_text(stmt)
        fp = sql_fingerprint(text)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)

        objects: list[str] = []
        stmt_joins: list[AbapJoin] = []

        if kind == "select":
            from_match = _RE_SELECT_FROM.search(stmt)
            left_table = ""
            if from_match:
                obj = _object_token(from_match.group(1), from_match.group(2), from_match.group(3), from_match.group(4))
                if obj:
                    objects.append(obj)
                    left_table = obj.split(".")[-1].strip('"').upper()
                    tables.add(left_table)

            for jm in _RE_JOIN.finditer(stmt):
                join_type = (jm.group(1) or "JOIN").strip().upper()
                obj = _object_token(jm.group(2), jm.group(3), jm.group(4), jm.group(5))
                condition = (jm.group(6) or "").strip()
                if obj:
                    objects.append(obj)
                    right = obj.split(".")[-1].strip('"').upper()
                    tables.add(right)
                    aj = AbapJoin(
                        table=right,
                        join_type=join_type.replace("  ", " "),
                        condition=condition,
                        left_table=left_table,
                        right_table=right,
                        line=line_no,
                    )
                    stmt_joins.append(aj)
                    joins.append(aj)

        for tm in _RE_TABLE_OPS.finditer(stmt):
            obj = _object_token(tm.group(2), None, tm.group(3), tm.group(4))
            if obj:
                objects.append(obj)
                tables.add(obj.split(".")[-1].strip('"').upper())

        where_m = _RE_WHERE.search(stmt)
        where_clause = (where_m.group(1).strip() if where_m else "")[:500]

        complexity = _compute_complexity(text, len(stmt_joins))
        stable_id = f"ABAP::SQL::{program}::{line_no}:{fp[:8]}"

        deduped_objects = list(dict.fromkeys(objects))
        sql_stmts.append(
            AbapSqlStatement(
                statement_kind=kind,
                source_type="OPEN_SQL",
                text=text,
                line=line_no,
                objects=deduped_objects,
                where_clause=where_clause,
                fingerprint=fp,
                stable_id=stable_id,
                confidence=1.0,
                dynamic_sql_risk=False,
                lineage_completeness="complete",
                complexity=complexity,
                ast_root=_build_ast(text, deduped_objects, where_clause, stmt_joins),
            )
        )

    return sql_stmts, joins, tables
