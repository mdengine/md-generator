from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin


class BwStubParser(SapParserPlugin):
    name = "bw.stub"
    version = "0.1.0"

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in {".adso", ".bwtr", ".compositeprovider"} or "adso" in path.name.lower()

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        from md_generator.sap.models.entities.kinds import SapObjectKind
        from md_generator.sap.models.entities.sap_object import SapObject
        from md_generator.sap.models.metadata.odata import SapObjectCategory

        obj = SapObject(
            kind=SapObjectKind.BW_OBJECT,
            name=path.stem,
            package="BW",
            description=f"BW artifact stub: {path.name}",
            source_path=path,
            raw_metadata={"bw": {"stub": True, "path": str(path)}},
            category=SapObjectCategory.METADATA,
        )
        return SapParseResult(path=path, objects=[obj], metadata={"stub": True})
