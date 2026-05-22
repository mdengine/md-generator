from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext, SapParseResult

_RE_SEGMENT = re.compile(r"SEGMENT\s+(\w+)", re.I)


class IdocParserPlugin:
    name = "idoc"

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        return "idoc" in n or n.startswith("we") or path.suffix.lower() in {".idoc", ".idoc.xml"}

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        text = path.read_text(encoding="utf-8", errors="replace")
        segments: list[str] = []
        if path.suffix.lower() == ".xml":
            try:
                tree = ET.parse(path)
                for elem in tree.iter():
                    if elem.tag.endswith("segment") or "segment" in elem.tag.lower():
                        nm = elem.get("name") or elem.text
                        if nm:
                            segments.append(nm.upper())
            except ET.ParseError:
                pass
        for m in _RE_SEGMENT.finditer(text):
            segments.append(m.group(1).upper())
        name = path.stem.upper()
        obj = SapObject(
            kind=SapObjectKind.IDOC,
            name=name,
            package=ctx.package_hint,
            source_path=path,
            raw_metadata={"idoc": {"name": name, "segments": sorted(set(segments))}},
            tags=["idoc"],
        )
        return SapParseResult(path=path, objects=[obj], metadata={"segments": segments})
