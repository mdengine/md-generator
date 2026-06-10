from __future__ import annotations

from typing import Literal

from md_generator.sap.models.entities.kinds import SapObjectKind

DdicObjectKind = Literal[
    "DATA_ELEMENT",
    "DOMAIN",
    "STRUCTURE",
    "TABLE",
    "TABLE_TYPE",
    "RANGE_TYPE",
    "REFERENCE_TYPE",
]

SAP_TYPE_KIND_TO_DDIC: dict[str, DdicObjectKind] = {
    "domain": "DOMAIN",
    "structure": "STRUCTURE",
    "tabletype": "TABLE_TYPE",
    "table": "TABLE",
    "rangetype": "RANGE_TYPE",
    "referencetype": "REFERENCE_TYPE",
    "reference": "REFERENCE_TYPE",
    "dataelement": "DATA_ELEMENT",
}

KIND_TO_SAP_OBJECT: dict[DdicObjectKind, SapObjectKind] = {
    "DATA_ELEMENT": SapObjectKind.DATA_ELEMENT,
    "DOMAIN": SapObjectKind.DOMAIN,
    "STRUCTURE": SapObjectKind.STRUCTURE,
    "TABLE": SapObjectKind.TABLE,
    "TABLE_TYPE": SapObjectKind.TABLE_TYPE,
    "RANGE_TYPE": SapObjectKind.RANGE_TYPE,
    "REFERENCE_TYPE": SapObjectKind.REFERENCE_TYPE,
}

KIND_TO_METADATA_KEY: dict[DdicObjectKind, str] = {
    "DATA_ELEMENT": "data_element",
    "DOMAIN": "domain",
    "STRUCTURE": "structure",
    "TABLE": "ddic",
    "TABLE_TYPE": "table_type",
    "RANGE_TYPE": "range_type",
    "REFERENCE_TYPE": "reference_type",
}

KIND_TO_ARTIFACT_TYPE: dict[DdicObjectKind, str] = {
    "DATA_ELEMENT": "ddic.data_element",
    "DOMAIN": "ddic.domain",
    "STRUCTURE": "ddic.structure",
    "TABLE": "ddic.table",
    "TABLE_TYPE": "ddic.table_type",
    "RANGE_TYPE": "ddic.range_type",
    "REFERENCE_TYPE": "ddic.reference_type",
}


def ddic_kind_from_type_kind(type_kind: str) -> DdicObjectKind | None:
    return SAP_TYPE_KIND_TO_DDIC.get(type_kind.replace("_", "").lower())
