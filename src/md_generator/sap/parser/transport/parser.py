from __future__ import annotations

import csv
from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext, SapParseResult


class TransportParserPlugin:
    name = "transport"

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        return "transport" in n or "cotr" in n or path.suffix.lower() in {".co", ".tr", ".transport"}

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        objects: list[SapObject] = []
        entries: list[dict] = []
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".csv":
            reader = csv.DictReader(text.splitlines())
            for row in reader:
                norm = {k.strip().upper(): (v or "").strip() for k, v in row.items() if k}
                obj_name = norm.get("OBJECT") or norm.get("OBJ_NAME") or norm.get("PGMID") or ""
                obj_type = norm.get("OBJECT_TYPE") or norm.get("TYPE") or "TRANSPORT"
                if not obj_name:
                    continue
                entries.append({"name": obj_name, "type": obj_type})
                objects.append(
                    SapObject(
                        kind=SapObjectKind.TRANSPORT_OBJECT,
                        name=obj_name.upper(),
                        package=norm.get("DEVCLASS") or ctx.package_hint,
                        source_path=path,
                        raw_metadata={"transport": norm},
                        tags=["transport"],
                    )
                )
        else:
            for line in text.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    entries.append({"name": parts[0], "type": parts[1]})
                    objects.append(
                        SapObject(
                            kind=SapObjectKind.TRANSPORT_OBJECT,
                            name=parts[0].upper(),
                            package=ctx.package_hint,
                            source_path=path,
                            raw_metadata={"transport": {"line": line.strip()}},
                            tags=["transport"],
                        )
                    )
        return SapParseResult(path=path, objects=objects, metadata={"transport_entries": entries})
