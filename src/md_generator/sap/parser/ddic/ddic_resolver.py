from __future__ import annotations

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.ddic_kinds import (
    DdicObjectKind,
    KIND_TO_METADATA_KEY,
    KIND_TO_SAP_OBJECT,
    ddic_kind_from_type_kind,
)


def _by_name(objects: list[SapObject]) -> dict[str, SapObject]:
    return {obj.name.upper(): obj for obj in objects}


def _kind_for_object(obj: SapObject) -> DdicObjectKind | None:
    adt = (obj.raw_metadata or {}).get("adt_ddic") or {}
    ok = adt.get("ddic_object_kind") or adt.get("object_type")
    if ok in KIND_TO_SAP_OBJECT:
        return ok  # type: ignore[return-value]
    mapping = {
        SapObjectKind.DATA_ELEMENT: "DATA_ELEMENT",
        SapObjectKind.DOMAIN: "DOMAIN",
        SapObjectKind.STRUCTURE: "STRUCTURE",
        SapObjectKind.TABLE: "TABLE",
        SapObjectKind.TABLE_TYPE: "TABLE_TYPE",
        SapObjectKind.RANGE_TYPE: "RANGE_TYPE",
        SapObjectKind.REFERENCE_TYPE: "REFERENCE_TYPE",
        SapObjectKind.CDS_STRUCTURE: "STRUCTURE",
    }
    return mapping.get(obj.kind)  # type: ignore[return-value]


def resolve_ddic_type_name(
    type_kind: str,
    type_name: str,
    by_name: dict[str, SapObject],
) -> tuple[SapObject | None, str]:
    """Resolve data element type_name to an object in the run; returns (obj, resolution_strategy)."""
    target = type_name.upper()
    if not target:
        return None, "unresolved"
    if target in by_name:
        return by_name[target], "same_run_name_match"
    expected = ddic_kind_from_type_kind(type_kind)
    for obj in by_name.values():
        if obj.name.upper() != target:
            continue
        if expected is None or _kind_for_object(obj) == expected:
            return obj, "same_run_kind_match"
    return None, "unresolved"


def enrich_ddic_objects_in_run(objects: list[SapObject]) -> None:
    """Attach resolved_type references on data elements when targets exist in the run."""
    by_name = _by_name(objects)
    for obj in objects:
        if obj.kind != SapObjectKind.DATA_ELEMENT:
            continue
        meta = (obj.raw_metadata or {}).get("data_element")
        if not isinstance(meta, dict):
            continue
        type_kind = meta.get("type_kind", "")
        type_name = meta.get("type_name", "")
        resolved, strategy = resolve_ddic_type_name(type_kind, type_name, by_name)
        if resolved:
            meta["resolved_type"] = {
                "target": type_name,
                "object_id": resolved.object_id,
                "ddic_object_kind": _kind_for_object(resolved),
                "resolution_strategy": strategy,
            }
