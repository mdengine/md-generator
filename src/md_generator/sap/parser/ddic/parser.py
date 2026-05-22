from __future__ import annotations

import csv
import re
from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.ddic import DdicField, DdicTable
from md_generator.sap.analyzer.semantics.entity_mapper import infer_semantic_entity
from md_generator.sap.parser.base import ParseContext, SapParseResult


def _infer_business_name(field_name: str, domain: str) -> str:
    base = infer_semantic_entity(field_name, None)
    if domain:
        return f"{base} ({domain})"
    return base


def parse_ddic_csv(path: Path) -> list[DdicTable]:
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames:
        return []
    tables: dict[str, DdicTable] = {}
    name_lower = path.name.lower()
    is_dd03 = "dd03" in name_lower or "field" in (reader.fieldnames[0] or "").lower()

    for row in reader:
        norm = {k.strip().upper(): (v or "").strip() for k, v in row.items() if k}
        tabname = norm.get("TABNAME") or norm.get("TABLE") or norm.get("OBJ_NAME") or ""
        if not tabname:
            continue
        if tabname not in tables:
            tables[tabname] = DdicTable(name=tabname.upper())
        tbl = tables[tabname]
        if is_dd03 or norm.get("FIELDNAME") or norm.get("FIELD"):
            fname = norm.get("FIELDNAME") or norm.get("FIELD") or ""
            if not fname:
                continue
            domain = norm.get("DOMNAME") or norm.get("DOMAIN") or ""
            dtype = norm.get("DATATYPE") or norm.get("ROLLNAME") or ""
            key = norm.get("KEYFLAG") == "X" or norm.get("KEY") == "X"
            check = norm.get("CHECKTABLE") or norm.get("CHECK_TABLE") or ""
            fld = DdicField(
                name=fname.upper(),
                data_type=dtype,
                key=key,
                domain=domain.upper(),
                check_table=check.upper(),
                business_name=_infer_business_name(fname, domain),
            )
            tbl.fields.append(fld)
            if key and fname.upper() not in tbl.primary_key:
                tbl.primary_key.append(fname.upper())
        else:
            desc = norm.get("DDTEXT") or norm.get("DESCRIPTION") or ""
            if desc:
                tbl.description = desc
    return list(tables.values())


class DdicParserPlugin:
    name = "ddic"

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        if "dd02" in n or "dd03" in n:
            return path.suffix.lower() in {".csv", ".txt", ".tab"}
        return path.suffix.lower() in {".dd02l", ".dd03l", ".tabl"}

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        tables = parse_ddic_csv(path)
        objects: list[SapObject] = []
        meta_tables: list[dict] = []
        for tbl in tables:
            sem = infer_semantic_entity(tbl.name, None)
            obj = SapObject(
                kind=SapObjectKind.TABLE,
                name=tbl.name,
                package=ctx.package_hint,
                source_path=path,
                raw_metadata={"ddic": tbl.to_dict()},
                semantic_entity=sem,
                tags=["ddic", "table"],
            )
            objects.append(obj)
            meta_tables.append(tbl.to_dict())
        return SapParseResult(
            path=path,
            objects=objects,
            metadata={"ddic_tables": meta_tables},
        )
