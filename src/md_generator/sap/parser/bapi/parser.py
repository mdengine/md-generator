from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext, SapParseResult


def _parse_bapi_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_bapi_xml(path: Path) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    name = root.get("name") or root.findtext(".//name") or path.stem
    params = []
    for p in root.iter():
        if p.tag.endswith("param") or p.tag.endswith("parameter"):
            params.append({"name": p.get("name"), "type": p.get("type")})
    return {"name": name, "parameters": params}


class BapiParserPlugin:
    name = "bapi"

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        return "bapi" in n and path.suffix.lower() in {".json", ".xml"}

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        if path.suffix.lower() == ".json":
            data = _parse_bapi_json(path)
        else:
            data = _parse_bapi_xml(path)
        name = str(data.get("name") or data.get("bapi") or path.stem).upper()
        obj = SapObject(
            kind=SapObjectKind.BAPI,
            name=name,
            package=ctx.package_hint,
            source_path=path,
            raw_metadata={"bapi": data},
            tags=["bapi"],
        )
        return SapParseResult(path=path, objects=[obj], metadata={"bapi": data})
