from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.ddic.ddl_table_parser import parse_ddl_table


def resolve_adt_ddl_sidecar(xml_path: Path, table_name: str = "") -> Path | None:
    names = []
    if table_name:
        names.append(table_name.lower())
    stem = xml_path.stem
    if stem.endswith(".tabl"):
        stem = stem[: -len(".tabl")]
    names.append(stem.lower())
    parent = xml_path.parent
    seen: set[str] = set()
    for base in names:
        if base in seen:
            continue
        seen.add(base)
        for suffix in (".asddls", ".ddl"):
            candidate = parent / f"{base}{suffix}"
            if candidate.is_file():
                return candidate
    return None


def parse_adt_ddl_sidecar(path: Path, table_name: str) -> dict | None:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    tbl = parse_ddl_table(source, table_name, definition_source="adt_ddl_sidecar")
    if not tbl.fields:
        return None
    return tbl.to_dict()
