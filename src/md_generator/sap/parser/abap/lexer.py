from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class Token:
    kind: str
    value: str
    line: int


_COMMENT_LINE = re.compile(r"^\s*\*")
_STRING_DQ = re.compile(r'"([^"]|"")*"')


def strip_comments_and_strings(source: str) -> str:
    """Return ABAP source with comments and string literals blanked for pattern matching."""
    lines: list[str] = []
    for i, raw in enumerate(source.splitlines(), start=1):
        line = raw
        if _COMMENT_LINE.match(line):
            lines.append("")
            continue
        if '"' in line:
            line = _STRING_DQ.sub(lambda m: " " * len(m.group(0)), line)
        if "|" in line:
            parts = line.split("|")
            out_parts: list[str] = []
            in_str = False
            for j, part in enumerate(parts):
                if j == 0:
                    out_parts.append(part)
                    in_str = part.count('"') % 2 == 1
                elif in_str:
                    out_parts.append("|" + part)
                    in_str = part.count('"') % 2 == 1
                else:
                    out_parts.append(" " * (len(part) + 1))
            line = "".join(out_parts) if len(out_parts) > 1 else line
        lines.append(line)
    return "\n".join(lines)


def iter_statements(source: str) -> list[tuple[int, str]]:
    """Split ABAP into logical statement lines (period-terminated or key statement starts)."""
    cleaned = strip_comments_and_strings(source)
    statements: list[tuple[int, str]] = []
    buf: list[str] = []
    start_line = 1
    for i, raw in enumerate(cleaned.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if not buf:
            start_line = i
        buf.append(stripped)
        joined = " ".join(buf)
        if joined.endswith("."):
            statements.append((start_line, joined.rstrip(".").strip()))
            buf = []
        elif _starts_new_statement(stripped) and len(buf) > 1:
            prev = " ".join(buf[:-1])
            if prev:
                statements.append((start_line, prev))
            buf = [stripped]
            start_line = i
    if buf:
        statements.append((start_line, " ".join(buf)))
    return statements


def _starts_new_statement(line: str) -> bool:
    upper = line.upper()
    keys = (
        "SELECT ", "UPDATE ", "INSERT ", "DELETE ", "MODIFY ",
        "EXEC SQL", "ENDEXEC",
        "LOOP ", "READ TABLE", "AUTHORITY-CHECK", "CALL FUNCTION",
        "CALL METHOD", "PERFORM ", "INCLUDE ", "TYPES ", "DATA ",
        "CHECK ", "IF ", "MESSAGE ",
    )
    return any(upper.startswith(k) for k in keys)


def extract_exec_sql_blocks(source: str) -> list[tuple[int, str]]:
    """Extract EXEC SQL ... ENDEXEC blocks as (start_line, inner_sql).

    Uses comment stripping only (preserves quoted schema/object names).
    """
    lines = source.splitlines()
    blocks: list[tuple[int, str]] = []
    in_block = False
    start_line = 0
    buf: list[str] = []
    for i, raw in enumerate(lines, start=1):
        if _COMMENT_LINE.match(raw):
            continue
        stripped = raw.strip()
        if not stripped:
            continue
        upper = stripped.upper()
        if upper.startswith("EXEC SQL"):
            in_block = True
            start_line = i
            buf = [stripped]
            if "ENDEXEC" in upper:
                blocks.append((start_line, " ".join(buf)))
                in_block = False
                buf = []
            continue
        if in_block:
            buf.append(stripped)
            if "ENDEXEC" in upper:
                blocks.append((start_line, " ".join(buf)))
                in_block = False
                buf = []
    return blocks
