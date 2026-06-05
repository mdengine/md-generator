from __future__ import annotations

from md_generator.sap.markdown.resolved_link import confidence_for_strategy
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
                "confidence": confidence_for_strategy(strategy),
            }
    expand_nested_structures(objects)


def expand_nested_structures(objects: list[SapObject]) -> None:
    structures: dict[str, list[dict]] = {}
    for obj in objects:
        if obj.kind != SapObjectKind.STRUCTURE:
            continue
        meta = (obj.raw_metadata or {}).get("structure")
        if isinstance(meta, dict):
            structures[obj.name.upper()] = list(meta.get("components") or [])

    def _expand(comps: list[dict], visited: set[str]) -> list[dict]:
        out: list[dict] = []
        for raw in comps:
            comp = dict(raw)
            include = (comp.get("include_structure") or "").upper()
            type_name = (comp.get("type_name") or include).upper()
            if include or str(comp.get("type_kind", "")).lower() == "structure":
                comp["type_kind"] = "structure"
                comp["type_name"] = type_name or include
                target = type_name or include
                if target in visited:
                    comp["cycle_detected"] = True
                    comp["cycle_path"] = list(visited) + [target]
                elif target in structures:
                    child_visited = set(visited)
                    child_visited.add(target)
                    comp["children"] = _expand(structures[target], child_visited)
            elif comp.get("children"):
                comp["children"] = _expand(list(comp["children"]), set(visited))
            out.append(comp)
        return out

    for obj in objects:
        if obj.kind != SapObjectKind.STRUCTURE:
            continue
        meta = (obj.raw_metadata or {}).get("structure")
        if isinstance(meta, dict):
            meta["components"] = _expand(list(meta.get("components") or []), {obj.name.upper()})
