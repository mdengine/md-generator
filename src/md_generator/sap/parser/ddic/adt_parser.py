from __future__ import annotations

from pathlib import Path

from md_generator.sap.analyzer.semantics.entity_mapper import infer_semantic_entity
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext, SapParseResult
from md_generator.sap.parser.ddic.adt_xml import is_adt_ddic_xml, parse_adt_ddic_file


class AdtDdicParserPlugin:
    name = "ddic.adt"

    def can_parse(self, path: Path) -> bool:
        return is_adt_ddic_xml(path)

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        parsed = parse_adt_ddic_file(path)
        if not parsed:
            return SapParseResult(path=path, objects=[], metadata={})

        kind_key = parsed["object_kind"]
        if kind_key == "DATA_ELEMENT":
            meta = parsed["data_element"]
            obj_kind = SapObjectKind.DATA_ELEMENT
            tag = "data_element"
            raw_key = "data_element"
        elif kind_key == "DOMAIN":
            meta = parsed["domain"]
            obj_kind = SapObjectKind.DOMAIN
            tag = "domain"
            raw_key = "domain"
        else:
            meta = parsed["ddic"]
            obj_kind = SapObjectKind.TABLE
            tag = "table"
            raw_key = "ddic"

        name = meta["name"]
        package = meta.get("package") or ctx.package_hint
        sem = infer_semantic_entity(name, None)
        obj = SapObject(
            kind=obj_kind,
            name=name,
            package=package,
            description=meta.get("description", ""),
            source_path=path,
            raw_metadata={raw_key: meta, "adt_ddic": {"object_type": kind_key, "source": "adt_xml"}},
            semantic_entity=sem,
            tags=["ddic", "adt", tag],
        )
        return SapParseResult(
            path=path,
            objects=[obj],
            metadata={"adt_ddic": parsed},
        )
