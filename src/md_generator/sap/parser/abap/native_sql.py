from __future__ import annotations

import re

from md_generator.sap.models.metadata.abap import (
    AbapSqlStatement,
    DynamicSqlSignal,
    SqlAstNode,
    SqlComplexity,
)
from md_generator.sap.parser.abap.lexer import extract_exec_sql_blocks
from md_generator.sap.parser.abap.sql_extractor import _RE_JOIN, _RE_SELECT_FROM, _RE_TABLE_OPS, _RE_WHERE
from md_generator.sap.parser.abap.sql_fingerprint import sql_fingerprint
from md_generator.sap.parser.abap.view_classifier import parse_schema_qualified

_RE_ADBC_PREPARE = re.compile(
    r"(?:prepare_statement|execute_query)\s*\(\s*['\"](.+?)['\"]",
    re.I | re.S,
)
_RE_SQL_ASSIGN = re.compile(
    r"(?:lv_sql|sql_text|lv_query|l_sql)\s*=\s*['\"](.+?)['\"]",
    re.I | re.S,
)
_RE_EXECUTE_IMMEDIATE = re.compile(r"\bEXECUTE\s+IMMEDIATE\b", re.I)
_RE_DYNAMIC_CONCAT = re.compile(
    r"(?:CONCATENATE|lv_sql\s*=).+(?:SELECT|FROM|INSERT|UPDATE|DELETE)",
    re.I,
)


def detect_dynamic_sql(source: str) -> list[DynamicSqlSignal]:
    signals: list[DynamicSqlSignal] = []
    for i, line in enumerate(source.splitlines(), start=1):
        if _RE_EXECUTE_IMMEDIATE.search(line):
            signals.append(DynamicSqlSignal(pattern="EXECUTE IMMEDIATE", line=i))
        if _RE_DYNAMIC_CONCAT.search(line):
            signals.append(DynamicSqlSignal(pattern="dynamic_sql_concat", line=i))
    return signals


def _extract_objects_from_sql(sql: str) -> list[str]:
    objects: list[str] = []
    for m in _RE_SELECT_FROM.finditer(sql):
        if m.group(3) and m.group(4):
            objects.append(f'"{m.group(3)}"."{m.group(4)}"')
        elif m.group(1):
            objects.append(m.group(1).upper())
    for jm in _RE_JOIN.finditer(sql):
        if jm.group(4) and jm.group(5):
            objects.append(f'"{jm.group(4)}"."{jm.group(5)}"')
        elif jm.group(2):
            objects.append(jm.group(2).upper())
    for tm in _RE_TABLE_OPS.finditer(sql):
        if tm.group(3) and tm.group(4):
            objects.append(f'"{tm.group(3)}"."{tm.group(4)}"')
        elif tm.group(2):
            objects.append(tm.group(2).upper())
    return list(dict.fromkeys(objects))


def _make_native_stmt(
    sql: str,
    line: int,
    program: str,
    source_type: str,
    confidence: float,
    dynamic: bool,
) -> AbapSqlStatement:
    text = re.sub(r"\s+", " ", sql.strip())[:2048]
    fp = sql_fingerprint(text)
    objects = _extract_objects_from_sql(text)
    where_m = _RE_WHERE.search(text)
    where = (where_m.group(1).strip() if where_m else "")[:500]
    join_count = len(_RE_JOIN.findall(text))
    subquery_count = len(re.findall(r"\(\s*SELECT\b", text, re.I))
    return AbapSqlStatement(
        statement_kind="select" if text.upper().lstrip().startswith("SELECT") else "other",
        source_type=source_type,  # type: ignore[arg-type]
        text=text,
        line=line,
        objects=objects,
        where_clause=where,
        fingerprint=fp,
        stable_id=f"ABAP::SQL::{program}::{line}:{fp[:8]}",
        confidence=confidence,
        dynamic_sql_risk=dynamic,
        lineage_completeness="partial" if dynamic else ("partial" if confidence < 0.8 else "complete"),
        complexity=SqlComplexity(
            join_count=join_count,
            subquery_count=subquery_count,
            complexity_score=round(min(10.0, join_count * 1.5 + subquery_count * 2.0), 2),
        ),
        ast_root=SqlAstNode(
            node_kind="select",
            value=text[:120],
            children=[SqlAstNode(node_kind="object_ref", value=o) for o in objects],
        ),
    )


def extract_native_sql(source: str, program: str) -> tuple[list[AbapSqlStatement], list[tuple[str, int]]]:
    """Extract EXEC SQL, ADBC, and inferred dynamic SQL statements."""
    stmts: list[AbapSqlStatement] = []
    object_lines: list[tuple[str, int]] = []
    seen_fp: set[str] = set()

    for line_no, block in extract_exec_sql_blocks(source):
        inner = re.sub(r"^\s*EXEC\s+SQL\s*", "", block, flags=re.I).strip()
        inner = re.sub(r"\s*ENDEXEC\.?\s*$", "", inner, flags=re.I).strip()
        if not inner:
            continue
        fp = sql_fingerprint(inner)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        stmt = _make_native_stmt(inner, line_no, program, "EXEC_SQL", 0.95, False)
        stmts.append(stmt)
        for obj in stmt.objects:
            object_lines.append((obj, line_no))

    cleaned = source
    for m in _RE_ADBC_PREPARE.finditer(cleaned):
        sql = m.group(1)
        if "SELECT" not in sql.upper() and "FROM" not in sql.upper():
            continue
        fp = sql_fingerprint(sql)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        line = source[: m.start()].count("\n") + 1
        stmt = _make_native_stmt(sql, line, program, "ADBC", 0.6, False)
        stmts.append(stmt)
        for obj in stmt.objects:
            object_lines.append((obj, line))

    for m in _RE_SQL_ASSIGN.finditer(cleaned):
        sql = m.group(1)
        if "SELECT" not in sql.upper() and "FROM" not in sql.upper():
            continue
        fp = sql_fingerprint(sql)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        line = source[: m.start()].count("\n") + 1
        stmt = _make_native_stmt(sql, line, program, "DYNAMIC_SQL", 0.55, True)
        stmts.append(stmt)
        for obj in stmt.objects:
            object_lines.append((obj, line))

    return stmts, object_lines
