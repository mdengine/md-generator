from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from md_generator.sap.analyzer.semantics.entity_mapper import infer_semantic_entity
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.ddic_kinds import (
    DdicObjectKind,
    KIND_TO_METADATA_KEY,
    KIND_TO_SAP_OBJECT,
)
from md_generator.sap.parser.base import ParseContext, SapParseResult


def is_abapgit_tabl_xml(path: Path) -> bool:
    if path.suffix.lower() != ".xml":
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:8192]
    except OSError:
        return False
    lower = head.lower()
    return "abapgit version" in lower and "lcl_object_tabl" in lower


def _local(tag: str) -> str:
    if not isinstance(tag, str):
        return str(tag)
    return tag.split("}")[-1] if "}" in tag else tag


def _child_text(parent: ET.Element, local_name: str, default: str = "") -> str:
    for child in parent:
        if _local(child.tag) == local_name:
            return (child.text or "").strip()
    return default


def _int_text(parent: ET.Element, local_name: str, default: int = 0) -> int:
    raw = _child_text(parent, local_name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def parse_abapgit_tabl_xml(text: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None

    dd02v = None
    dd03p = None
    for elem in root.iter():
        tag = _local(elem.tag)
        if tag == "DD02V":
            dd02v = elem
        elif tag == "DD03P_TABLE":
            dd03p = elem

    if dd02v is None:
        return None

    name = _child_text(dd02v, "TABNAME").upper()
    if not name:
        return None
    description = _child_text(dd02v, "DDTEXT")
    tabclass = _child_text(dd02v, "TABCLASS").upper()
    package = _child_text(dd02v, "CONT_FLAG")

    fields: list[dict[str, Any]] = []
    if dd03p is not None:
        for row in dd03p:
            if _local(row.tag) != "DD03P":
                continue
            fname = _child_text(row, "FIELDNAME").upper()
            if not fname or fname.startswith("."):
                continue
            key = _child_text(row, "KEYFLAG").upper() == "X"
            fields.append({
                "name": fname,
                "data_element": _child_text(row, "ROLLNAME").upper(),
                "data_type": _child_text(row, "DATATYPE"),
                "length": _int_text(row, "LENG"),
                "key": key,
                "domain": _child_text(row, "DOMNAME").upper(),
                "check_table": _child_text(row, "CHECKTABLE").upper(),
            })

    if tabclass == "INTTAB":
        components = [
            {
                "name": f["name"],
                "data_element": f.get("data_element", ""),
                "data_type": f.get("data_type", ""),
                "length": f.get("length", 0),
            }
            for f in fields
        ]
        return {
            "object_kind": "STRUCTURE",
            "structure": {
                "name": name,
                "description": description,
                "package": package,
                "components": components,
                "definition_source": "abapgit_tabl",
            },
        }

    return {
        "object_kind": "TABLE",
        "ddic": {
            "name": name,
            "description": description,
            "package": package,
            "fields": fields,
            "primary_key": [f["name"] for f in fields if f.get("key")],
            "definition_source": "abapgit_tabl",
            "table_type": tabclass,
        },
    }


class AbapGitTablParserPlugin:
    name = "ddic.abapgit_tabl"

    def can_parse(self, path: Path) -> bool:
        return is_abapgit_tabl_xml(path)

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        parsed = parse_abapgit_tabl_xml(path.read_text(encoding="utf-8", errors="replace"))
        if not parsed:
            return SapParseResult(path=path, objects=[], metadata={})

        kind_key: DdicObjectKind = parsed["object_kind"]  # type: ignore[assignment]
        raw_key = KIND_TO_METADATA_KEY[kind_key]
        meta = parsed[raw_key]
        obj_kind = KIND_TO_SAP_OBJECT[kind_key]
        name = meta["name"]
        sem = infer_semantic_entity(name, None)
        obj = SapObject(
            kind=obj_kind,
            name=name,
            package=meta.get("package") or ctx.package_hint,
            description=meta.get("description", ""),
            source_path=path,
            raw_metadata={
                raw_key: meta,
                "adt_ddic": {
                    "ddic_object_kind": kind_key,
                    "object_type": kind_key,
                    "source": "abapgit_tabl",
                },
            },
            semantic_entity=sem,
            tags=["ddic", "abapgit", raw_key.replace("_", "-")],
        )
        return SapParseResult(path=path, objects=[obj], metadata={"abapgit_tabl": parsed})
