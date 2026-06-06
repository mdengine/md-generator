from __future__ import annotations

from typing import Any

from md_generator.sap.models.metadata.ddic_canonical import (
    DataElementMetadata,
    DdicCanonicalMetadata,
    DdicCanonicalPayload,
    DomainMetadata,
    RangeTypeMetadata,
    ReferenceTypeMetadata,
    StructureComponentMetadata,
    StructureMetadata,
    TableFieldMetadata,
    TableMetadata,
    TableTypeMetadata,
)
from md_generator.sap.models.metadata.ddic_kinds import DdicObjectKind

KIND_TO_LEGACY_KEY: dict[DdicObjectKind, str] = {
    "DATA_ELEMENT": "data_element",
    "DOMAIN": "domain",
    "STRUCTURE": "structure",
    "TABLE": "ddic",
    "TABLE_TYPE": "table_type",
    "RANGE_TYPE": "range_type",
    "REFERENCE_TYPE": "reference_type",
}


def _component_from_dict(raw: dict) -> StructureComponentMetadata:
    return StructureComponentMetadata(
        name=raw.get("name", ""),
        data_element=raw.get("data_element", ""),
        type_kind=raw.get("type_kind", ""),
        type_name=raw.get("type_name", ""),
        data_type=raw.get("data_type", ""),
        length=int(raw.get("length") or 0),
        include_structure=raw.get("include_structure", ""),
        children=[_component_from_dict(c) for c in raw.get("children") or []],
        cycle_detected=bool(raw.get("cycle_detected")),
        cycle_path=list(raw.get("cycle_path") or []),
    )


def _component_to_dict(comp: StructureComponentMetadata) -> dict[str, Any]:
    d: dict[str, Any] = {
        "name": comp.name,
        "data_element": comp.data_element,
        "type_kind": comp.type_kind,
        "type_name": comp.type_name,
        "data_type": comp.data_type,
        "length": comp.length,
    }
    if comp.include_structure:
        d["include_structure"] = comp.include_structure
    if comp.children:
        d["children"] = [_component_to_dict(c) for c in comp.children]
    if comp.cycle_detected:
        d["cycle_detected"] = True
        d["cycle_path"] = list(comp.cycle_path)
    return d


def payload_from_data_element(meta: dict) -> DataElementMetadata:
    return DataElementMetadata(
        type_kind=meta.get("type_kind", ""),
        type_name=meta.get("type_name", ""),
        data_type=meta.get("data_type", ""),
        data_type_length=int(meta.get("data_type_length") or 0),
        data_type_decimals=int(meta.get("data_type_decimals") or 0),
    )


def payload_from_domain(meta: dict) -> DomainMetadata:
    return DomainMetadata(
        data_type=meta.get("data_type", ""),
        length=int(meta.get("length") or 0),
        decimals=int(meta.get("decimals") or 0),
        value_table=meta.get("value_table", ""),
    )


def payload_from_structure(meta: dict) -> StructureMetadata:
    return StructureMetadata(
        definition_source=meta.get("definition_source", "adt_xml"),
        components=[_component_from_dict(c) for c in meta.get("components") or []],
    )


def payload_from_table(meta: dict) -> TableMetadata:
    fields = [
        TableFieldMetadata(
            name=f.get("name", ""),
            data_element=f.get("data_element", ""),
            data_type=f.get("data_type", ""),
            length=int(f.get("length") or 0),
            key=bool(f.get("key")),
        )
        for f in meta.get("fields") or []
    ]
    return TableMetadata(
        definition_source=meta.get("definition_source", ""),
        table_type=meta.get("table_type", ""),
        fields=fields,
    )


def payload_from_table_type(meta: dict) -> TableTypeMetadata:
    return TableTypeMetadata(
        row_type=meta.get("row_type", ""),
        line_type=meta.get("line_type", ""),
        access_mode=meta.get("access_mode", ""),
    )


def payload_from_range_type(meta: dict) -> RangeTypeMetadata:
    return RangeTypeMetadata(
        data_element=meta.get("data_element", ""),
        domain=meta.get("domain", ""),
    )


def payload_from_reference_type(meta: dict) -> ReferenceTypeMetadata:
    return ReferenceTypeMetadata(
        referenced_type=meta.get("referenced_type", ""),
        check_table=meta.get("check_table", ""),
    )


_PAYLOAD_BUILDERS: dict[DdicObjectKind, Any] = {
    "DATA_ELEMENT": payload_from_data_element,
    "DOMAIN": payload_from_domain,
    "STRUCTURE": payload_from_structure,
    "TABLE": payload_from_table,
    "TABLE_TYPE": payload_from_table_type,
    "RANGE_TYPE": payload_from_range_type,
    "REFERENCE_TYPE": payload_from_reference_type,
}


def build_payload(object_kind: DdicObjectKind, meta: dict) -> DdicCanonicalPayload:
    builder = _PAYLOAD_BUILDERS[object_kind]
    return builder(meta)


def attach_ddic_canonical(
    metadata: dict,
    object_kind: DdicObjectKind,
    legacy_meta: dict,
    *,
    definition_source: str | None = None,
) -> None:
    src = definition_source or legacy_meta.get("definition_source", "adt_xml")
    metadata["ddic_canonical"] = DdicCanonicalMetadata(
        object_kind=object_kind,
        definition_source=src,
        payload=build_payload(object_kind, legacy_meta),
    ).model_dump(mode="json")


def parse_ddic_canonical(metadata: dict) -> DdicCanonicalMetadata | None:
    raw = metadata.get("ddic_canonical")
    if not raw:
        return None
    return DdicCanonicalMetadata.model_validate(raw)


def _merge_legacy(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    merged.update({k: v for k, v in overlay.items() if v not in (None, "", [], {})})
    return merged


def _legacy_from_payload(canonical: DdicCanonicalMetadata) -> dict[str, Any]:
    payload = canonical.payload
    if isinstance(payload, DataElementMetadata):
        return payload.model_dump()
    if isinstance(payload, DomainMetadata):
        return payload.model_dump()
    if isinstance(payload, StructureMetadata):
        return {
            "definition_source": payload.definition_source,
            "components": [_component_to_dict(c) for c in payload.components],
        }
    if isinstance(payload, TableMetadata):
        return {
            "definition_source": payload.definition_source,
            "table_type": payload.table_type,
            "fields": [f.model_dump() for f in payload.fields],
        }
    if isinstance(payload, TableTypeMetadata):
        return payload.model_dump()
    if isinstance(payload, RangeTypeMetadata):
        return payload.model_dump()
    if isinstance(payload, ReferenceTypeMetadata):
        return payload.model_dump()
    return {}


def resolve_ddic_meta(
    metadata: dict,
    object_kind: DdicObjectKind,
    *,
    name: str = "",
    package: str = "",
    description: str = "",
) -> dict[str, Any]:
    legacy_key = KIND_TO_LEGACY_KEY[object_kind]
    legacy = dict(metadata.get(legacy_key) or {})
    canonical = parse_ddic_canonical(metadata)
    if canonical and canonical.object_kind == object_kind:
        typed = _legacy_from_payload(canonical)
        for key in ("kind",):
            typed.pop(key, None)
        legacy = _merge_legacy(legacy, typed)
        if canonical.definition_source and not legacy.get("definition_source"):
            legacy["definition_source"] = canonical.definition_source
    if name and not legacy.get("name"):
        legacy["name"] = name
    if package and not legacy.get("package"):
        legacy["package"] = package
    if description and not legacy.get("description"):
        legacy["description"] = description
    return legacy
