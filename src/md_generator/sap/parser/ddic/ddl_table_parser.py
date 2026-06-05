from __future__ import annotations

import re

from md_generator.sap.models.metadata.ddic import DdicField, DdicTable

_RE_DEFINE_TABLE = re.compile(r"define\s+table\s+(\w+)", re.I)
_RE_TABLE_TYPE = re.compile(
    r"@AbapCatalog\.table\s+type\s*:\s*#(\w+)",
    re.I,
)
_RE_ANNOTATION = re.compile(
    r"@([\w.]+)\s*:\s*(?:#(\w+)|'([^']*)'|\"([^\"]*)\"|(\S+))",
    re.I,
)
_RE_FIELD = re.compile(
    r"^\s*(key\s+)?([\w/]+)\s*:\s*([\w/]+)\s*;",
    re.I | re.M,
)


def is_ddl_table_source(source: str) -> bool:
    return bool(_RE_DEFINE_TABLE.search(source))


def _extract_body(source: str) -> str:
    start = source.find("{")
    end = source.rfind("}")
    if start < 0 or end <= start:
        return ""
    return source[start + 1 : end]


def parse_ddl_table(source: str, fallback_name: str, *, definition_source: str = "ddl") -> DdicTable:
    name = fallback_name.upper()
    m = _RE_DEFINE_TABLE.search(source)
    if m:
        name = m.group(1).upper()

    table_type = ""
    tm = _RE_TABLE_TYPE.search(source)
    if tm:
        table_type = tm.group(1).upper()

    annotations: dict[str, str] = {}
    for am in _RE_ANNOTATION.finditer(source):
        key = am.group(1)
        value = am.group(2) or am.group(3) or am.group(4) or am.group(5) or ""
        annotations[key] = value.strip().lstrip("#")

    body = _extract_body(source)
    fields: list[DdicField] = []
    primary_key: list[str] = []

    for fm in _RE_FIELD.finditer(body):
        is_key = bool(fm.group(1))
        fname = fm.group(2).split("/")[-1].upper()
        data_element = fm.group(3).split("/")[-1].upper()
        fld = DdicField(
            name=fname,
            data_element=data_element,
            key=is_key,
        )
        fields.append(fld)
        if is_key and fname not in primary_key:
            primary_key.append(fname)

    return DdicTable(
        name=name,
        fields=fields,
        primary_key=primary_key,
        table_type=table_type,
        annotations=annotations,
        definition_source=definition_source,
    )
