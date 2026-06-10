from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.external._common import _emit_external, _ext_capabilities


class DbtManifestParser(SapParserPlugin):
    name = "external.dbt"
    version = "1.0.0"

    def capabilities(self):
        return _ext_capabilities(sql="yes")

    def can_parse(self, path: Path) -> bool:
        return path.name == "manifest.json" or (path.suffix == ".json" and "manifest" in path.name.lower())

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = json.loads(path.read_text(encoding="utf-8"))
        nodes = data.get("nodes", {})
        if not nodes:
            return None
        first_key = next(iter(nodes))
        node = nodes[first_key]
        name = node.get("name", path.stem)
        return _emit_external(
            path,
            artifact_type="external.dbt.model",
            namespace="DBT::",
            name=name,
            parser_id=self.name,
            metadata={"dbt": node, "resource_type": node.get("resource_type")},
        )
