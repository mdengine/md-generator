from __future__ import annotations

import re
from pathlib import Path

from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.abap import AbapAnalysis, AbapAuthCheck, AbapValidation
from md_generator.sap.parser.abap.lexer import iter_statements
from md_generator.sap.parser.abap.native_sql import detect_dynamic_sql, extract_native_sql
from md_generator.sap.parser.abap.sql_extractor import extract_open_sql_statements
from md_generator.sap.parser.abap.view_classifier import build_view_references
from md_generator.sap.parser.base import ParseContext, SapParseResult

_ABAP_SUFFIXES = {".abap", ".prog", ".asprog", ".inc"}

_RE_INTO_TABLE = re.compile(r"\bINTO\s+TABLE\s+@?(\w+)", re.I)
_RE_LOOP_TABLE = re.compile(r"\bLOOP AT\s+([\w/]+)", re.I)
_RE_READ_TABLE = re.compile(r"\bREAD TABLE\s+([\w/]+)", re.I)
_RE_CALL_FM = re.compile(r"CALL FUNCTION\s+'([^']+)'", re.I)
_RE_CALL_METHOD = re.compile(r"CALL METHOD\s+([\w=>\s]+)", re.I)
_RE_PERFORM = re.compile(r"\bPERFORM\s+(\w+)", re.I)
_RE_INCLUDE = re.compile(r"\bINCLUDE\s+([\w/]+)", re.I)
_RE_AUTH = re.compile(
    r"AUTHORITY-CHECK\s+OBJECT\s+'([^']+)'(.*?)(?:\.|$)",
    re.I | re.S,
)
_RE_AUTH_FIELD = re.compile(r"ID\s+'(\w+)'\s+FIELD\s+'([^']+)'", re.I)
_RE_IF_INITIAL = re.compile(r"\bIF\s+(.+?)\s+IS\s+INITIAL\b", re.I)
_RE_IF_COMPARE = re.compile(r"\bIF\s+(.+?)\s*([<>=]+)\s*(.+?)\.", re.I)
_RE_CHECK = re.compile(r"\bCHECK\s+(.+?)\.", re.I)
_RE_MESSAGE = re.compile(r"\bMESSAGE\s+(.+?)(?:\s+TYPE\s+\w)?\.", re.I)
_RE_DATA = re.compile(r"\bDATA\s*:?\s*([\w/]+)", re.I)
_RE_TYPES = re.compile(r"\bTYPES\s*:?\s*([\w/]+)", re.I)


def _program_name(path: Path) -> str:
    return path.stem.upper()


def parse_abap_source(source: str, program: str) -> AbapAnalysis:
    analysis = AbapAnalysis(program=program)
    stmts = iter_statements(source)

    sql_stmts, joins, sql_tables = extract_open_sql_statements(stmts, program)
    native_stmts, native_objects = extract_native_sql(source, program)
    analysis.sql_statements = sql_stmts + native_stmts
    analysis.joins = joins
    tables: set[str] = set(sql_tables)

    analysis.dynamic_sql_signals = detect_dynamic_sql(source)
    if analysis.dynamic_sql_signals:
        analysis.lineage_completeness = "partial"

    object_lines: list[tuple[str, int]] = []
    for s in analysis.sql_statements:
        for obj in s.objects:
            object_lines.append((obj, s.line))
    object_lines.extend(native_objects)
    analysis.view_references = build_view_references(object_lines)

    for line_no, stmt in stmts:
        upper = stmt.upper()

        for m in _RE_CALL_FM.finditer(stmt):
            analysis.functions.append(m.group(1).upper())
        for m in _RE_CALL_METHOD.finditer(stmt):
            analysis.methods.append(m.group(1).strip())
        for m in _RE_PERFORM.finditer(stmt):
            analysis.performs.append(m.group(1).upper())
        for m in _RE_INCLUDE.finditer(stmt):
            analysis.includes.append(m.group(1).upper())
        for m in _RE_DATA.finditer(stmt):
            analysis.data_declarations.append(m.group(1).upper())
        for m in _RE_TYPES.finditer(stmt):
            analysis.types_declarations.append(m.group(1).upper())

        if "AUTHORITY-CHECK" in upper:
            am = _RE_AUTH.search(stmt)
            if am:
                fields: list[str] = []
                for fm in _RE_AUTH_FIELD.finditer(am.group(2)):
                    fields.append(f"{fm.group(1)}={fm.group(2)}")
                analysis.auth_checks.append(
                    AbapAuthCheck(object=am.group(1).upper(), fields=fields, line=line_no)
                )

        for m in _RE_INTO_TABLE.finditer(stmt):
            t = m.group(1).split("/")[-1].upper()
            if t not in ("DATA", "TABLE"):
                tables.add(t)
        for m in _RE_LOOP_TABLE.finditer(stmt):
            tables.add(m.group(1).split("/")[-1].upper())
        for m in _RE_READ_TABLE.finditer(stmt):
            t = m.group(1).split("/")[-1].upper()
            if t not in ("DATA", "TABLE"):
                tables.add(t)

        if _RE_IF_INITIAL.search(stmt):
            analysis.validations.append(
                AbapValidation(rule_type="initial_check", expression=stmt[:200], line=line_no)
            )
        cm = _RE_IF_COMPARE.search(stmt)
        if cm:
            analysis.validations.append(
                AbapValidation(rule_type="comparison", expression=stmt[:200], line=line_no)
            )
        ck = _RE_CHECK.search(stmt)
        if ck:
            analysis.validations.append(
                AbapValidation(rule_type="check", expression=ck.group(1)[:200], line=line_no)
            )
        msg = _RE_MESSAGE.search(stmt)
        if msg:
            analysis.validations.append(
                AbapValidation(rule_type="message", expression=msg.group(1)[:200], line=line_no)
            )

    for ref in analysis.view_references:
        tables.add(ref.name)

    analysis.tables = sorted(tables)
    analysis.functions = sorted(set(analysis.functions))
    analysis.includes = sorted(set(analysis.includes))
    return analysis


def parse_abap_file(path: Path, *, stream_threshold_mb: int = 5) -> AbapAnalysis:
    program = _program_name(path)
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > stream_threshold_mb:
        chunks: list[str] = []
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                chunks.append(line)
        source = "".join(chunks)
    else:
        source = path.read_text(encoding="utf-8", errors="replace")
    return parse_abap_source(source, program)


class AbapParserPlugin:
    name = "abap"

    def capabilities(self) -> ParserCapability:
        return ParserCapability(lineage=True, sql_generation="partial", impact_analysis=True)

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in _ABAP_SUFFIXES

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        analysis = parse_abap_file(path)
        obj = SapObject(
            kind=SapObjectKind.PROGRAM,
            name=analysis.program,
            package=ctx.package_hint,
            source_path=path,
            raw_metadata={"abap": analysis.to_dict()},
            tags=["abap"],
        )
        return SapParseResult(path=path, objects=[obj], metadata={"abap": analysis.to_dict()})
