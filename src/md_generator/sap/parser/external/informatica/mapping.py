from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.external._common import _emit_external, _ext_capabilities
from md_generator.sap.parser.hana.xml_stream import iterparse_events, text


class InformaticaMappingParser(SapParserPlugin):
    name = "external.informatica"
    version = "1.0.0"

    def capabilities(self):
        return _ext_capabilities()

    def can_parse(self, path: Path) -> bool:
        if path.suffix.lower() != ".xml":
            return False
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:4096].lower()
        except OSError:
            return False
        return "informatica" in head or "mapping" in head and "powermart" in head

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        name = path.stem
        for tag, elem in iterparse_events(str(path), {"MAPPING", "Mapping"}):
            name = text(elem, "NAME", path.stem) or text(elem, "name", path.stem) or path.stem
            break
        return _emit_external(
            path,
            artifact_type="external.informatica.mapping",
            namespace="INFORMATICA::",
            name=name,
            parser_id=self.name,
            metadata={"mapping": name},
        )
