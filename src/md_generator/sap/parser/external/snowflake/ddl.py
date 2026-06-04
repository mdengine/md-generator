from __future__ import annotations

import re
from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.external._common import _emit_external, _ext_capabilities


class SnowflakeDdlParser(SapParserPlugin):
    name = "external.snowflake"
    version = "1.0.0"

    def capabilities(self):
        return _ext_capabilities(sql="yes")

    def can_parse(self, path: Path) -> bool:
        if path.suffix.lower() != ".sql":
            return False
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:2048].upper()
        except OSError:
            return False
        return "CREATE TABLE" in head or "CREATE VIEW" in head

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TABLE|VIEW)\s+([\\w.\"]+)", text, re.I)
        name = m.group(1).strip('"') if m else path.stem
        return _emit_external(
            path,
            artifact_type="external.snowflake.relation",
            namespace="SNOWFLAKE::",
            name=name,
            parser_id=self.name,
            metadata={"ddl_preview": text[:500]},
        )
