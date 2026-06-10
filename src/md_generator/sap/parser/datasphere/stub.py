from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin


class DatasphereStubParser(SapParserPlugin):
    name = "datasphere.stub"
    version = "0.1.0"

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in {".dsview", ".datasphere"} or "datasphere" in path.name.lower()

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        from md_generator.sap.models.entities.kinds import SapObjectKind
        from md_generator.sap.models.entities.sap_object import SapObject
        from md_generator.sap.models.metadata.odata import SapObjectCategory

        obj = SapObject(
            kind=SapObjectKind.DATASPHERE_OBJECT,
            name=path.stem,
            package="DATASPHERE",
            description=f"Datasphere artifact stub: {path.name}",
            source_path=path,
            raw_metadata={"datasphere": {"stub": True, "path": str(path)}},
            category=SapObjectCategory.METADATA,
        )
        return SapParseResult(path=path, objects=[obj], metadata={"stub": True})
