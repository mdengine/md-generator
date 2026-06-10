from __future__ import annotations

from pathlib import Path

from md_generator.sap.analyzer.semantics.entity_mapper import infer_semantic_entity
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.ddic_kinds import (
    DdicObjectKind,
    KIND_TO_METADATA_KEY,
    KIND_TO_SAP_OBJECT,
)
from md_generator.sap.parser.base import ParseContext, SapParseResult
from md_generator.sap.parser.ddic.adt_xml import is_adt_ddic_xml, parse_adt_ddic_file


def _build_object(
    kind: DdicObjectKind,
    meta: dict,
    path: Path,
    ctx: ParseContext,
) -> SapObject:
    raw_key = KIND_TO_METADATA_KEY[kind]
    obj_kind = KIND_TO_SAP_OBJECT[kind]
    tag = raw_key.replace("_", "-")
    name = meta["name"]
    package = meta.get("package") or ctx.package_hint
    sem = infer_semantic_entity(name, None)
    return SapObject(
        kind=obj_kind,
        name=name,
        package=package,
        description=meta.get("description", ""),
        source_path=path,
        raw_metadata={
            raw_key: meta,
            "adt_ddic": {
                "ddic_object_kind": kind,
                "object_type": kind,
                "source": "adt_xml",
            },
        },
        semantic_entity=sem,
        tags=["ddic", "adt", tag],
    )


class AdtDdicParserPlugin:
    name = "ddic.adt"

    def can_parse(self, path: Path) -> bool:
        return is_adt_ddic_xml(path)

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        parsed = parse_adt_ddic_file(path)
        if not parsed:
            return SapParseResult(path=path, objects=[], metadata={})

        kind_key: DdicObjectKind = parsed["object_kind"]  # type: ignore[assignment]
        raw_key = KIND_TO_METADATA_KEY[kind_key]
        meta = parsed[raw_key]
        obj = _build_object(kind_key, meta, path, ctx)
        return SapParseResult(path=path, objects=[obj], metadata={"adt_ddic": parsed})
