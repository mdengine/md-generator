from __future__ import annotations

from typing import Any


def format_open_sql(meta: dict[str, Any]) -> str:
    stmts = [s for s in meta.get("sql_statements", []) if s.get("source_type") == "OPEN_SQL"]
    if not stmts:
        return ""
    lines: list[str] = []
    for s in stmts[:20]:
        line = s.get("line", "?")
        fp = s.get("fingerprint", "")[:8]
        complexity = s.get("complexity", {})
        score = complexity.get("complexity_score", 0)
        lines.append(f"### Line {line} ({s.get('statement_kind', 'sql')}, score {score}, fp `{fp}`)")
        lines.append("```sql")
        lines.append(f"-- line {line}")
        lines.append(s.get("text", ""))
        lines.append("```")
        if s.get("where_clause"):
            lines.append(f"- WHERE: `{s['where_clause'][:200]}`")
    return "\n".join(lines)


def format_native_sql(meta: dict[str, Any]) -> str:
    stmts = [
        s
        for s in meta.get("sql_statements", [])
        if s.get("source_type") in ("EXEC_SQL", "ADBC", "DYNAMIC_SQL")
    ]
    if not stmts:
        return ""
    lines: list[str] = []
    for s in stmts[:20]:
        src = s.get("source_type", "?")
        conf = s.get("confidence", 0)
        risk = " (dynamic SQL risk)" if s.get("dynamic_sql_risk") else ""
        lines.append(f"### {src} — line {s.get('line', '?')} (confidence {conf}){risk}")
        lines.append("```sql")
        lines.append(s.get("text", ""))
        lines.append("```")
    return "\n".join(lines)


def format_joins(meta: dict[str, Any]) -> str:
    joins = meta.get("joins", [])
    if not joins:
        return ""
    lines: list[str] = []
    for j in joins[:40]:
        jt = j.get("join_type", "JOIN")
        left = j.get("left_table") or "?"
        right = j.get("right_table") or j.get("table", "?")
        cond = j.get("condition", "")
        line = j.get("line", "?")
        cond_part = f" ON `{cond}`" if cond else ""
        lines.append(f"- {jt} `{left}` → `{right}`{cond_part} (line {line})")
    return "\n".join(lines)


def format_view_refs(meta: dict[str, Any]) -> str:
    refs = meta.get("view_references", [])
    if not refs:
        return ""
    lines: list[str] = []
    for r in refs[:40]:
        name = r.get("name", "?")
        kind = r.get("kind", "unknown")
        conf = r.get("confidence", 0)
        schema = r.get("schema", "")
        label = f"{schema}.{name}" if schema else name
        res = r.get("resolution") or {}
        path = r.get("resolved_path") or res.get("resolved_path", "")
        strategy = res.get("resolution_strategy", "heuristic")
        if path:
            lines.append(f"- `{label}` — {kind} (confidence {conf}, {strategy}) → [{name}]({path})")
        else:
            lines.append(f"- `{label}` — {kind} (confidence {conf}, {strategy})")
    return "\n".join(lines)


def format_dynamic_sql_warnings(meta: dict[str, Any]) -> str:
    signals = meta.get("dynamic_sql_signals", [])
    completeness = meta.get("lineage_completeness", "complete")
    if not signals and completeness == "complete":
        return ""
    lines: list[str] = []
    if signals:
        lines.append("**Dynamic SQL detected — lineage may be incomplete.**")
        for sig in signals[:20]:
            lines.append(f"- `{sig.get('pattern')}` at line {sig.get('line', '?')}")
    if completeness != "complete":
        lines.append(f"- Lineage completeness: **{completeness}**")
    return "\n".join(lines)


def build_abap_program_markdown(name: str, meta: dict[str, Any]) -> str:
    sections = [f"# ABAP Program: {name}\n"]
    warn = format_dynamic_sql_warnings(meta)
    if warn:
        sections.append(f"## Warnings\n\n{warn}")
    open_sql = format_open_sql(meta)
    if open_sql:
        sections.append(f"## Open SQL\n\n{open_sql}")
    native = format_native_sql(meta)
    if native:
        sections.append(f"## Native SQL\n\n{native}")
    joins = format_joins(meta)
    if joins:
        sections.append(f"## Joins\n\n{joins}")
    tables = meta.get("tables", [])
    if tables:
        sections.append(f"## Related Tables\n\n{', '.join(f'`{t}`' for t in tables)}")
    views = format_view_refs(meta)
    if views:
        sections.append(f"## Views / CDS / HANA References\n\n{views}")
    return "\n\n".join(sections) + "\n"
