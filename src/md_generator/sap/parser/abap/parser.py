from __future__ import annotations

import re
from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.abap import AbapAnalysis, AbapAuthCheck, AbapJoin, AbapValidation
from md_generator.sap.parser.abap.lexer import iter_statements, strip_comments_and_strings
from md_generator.sap.parser.base import ParseContext, SapParseResult

_ABAP_SUFFIXES = {".abap", ".prog", ".asprog", ".inc"}

_RE_SELECT_FROM = re.compile(
    r"\bFROM\s+([\w/]+)",
    re.I,
)
_RE_JOIN = re.compile(
    r"\b(?:INNER|LEFT|RIGHT|FULL)?\s*JOIN\s+([\w/]+)",
    re.I,
)
_RE_TABLE_OPS = re.compile(
    r"\b(?:UPDATE|MODIFY|DELETE FROM|INSERT INTO)\s+([\w/]+)",
    re.I,
)
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
    tables: set[str] = set()

    for line_no, stmt in iter_statements(source):
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

        if upper.startswith("SELECT"):
            for m in _RE_SELECT_FROM.finditer(stmt):
                t = m.group(1).split("/")[-1].upper()
                tables.add(t)
            for m in _RE_JOIN.finditer(stmt):
                t = m.group(1).split("/")[-1].upper()
                tables.add(t)
                analysis.joins.append(AbapJoin(table=t, join_type="JOIN"))
        for m in _RE_TABLE_OPS.finditer(stmt):
            t = m.group(1).split("/")[-1].upper()
            if t not in ("TABLE", "DATA"):
                tables.add(t)
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
