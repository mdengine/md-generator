from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.external._common import _emit_external, _ext_capabilities


class KafkaSchemaParser(SapParserPlugin):
    name = "external.kafka"
    version = "1.0.0"

    def capabilities(self):
        return _ext_capabilities()

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in {".avsc", ".avro"}

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name", path.stem)
        return _emit_external(
            path,
            artifact_type="external.kafka.topic",
            namespace="KAFKA::",
            name=name,
            parser_id=self.name,
            metadata={"schema": data},
        )
