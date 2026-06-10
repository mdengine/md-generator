from __future__ import annotations

from enum import Enum


class SemanticTypeKind(str, Enum):
    SCALAR = "SCALAR"
    STRUCTURE = "STRUCTURE"
    TABLE_TYPE = "TABLE_TYPE"
    RANGE_TYPE = "RANGE_TYPE"
    REFERENCE = "REFERENCE"
    ENUM = "ENUM"
    DEEP = "DEEP"


_DDIC_TYPE_KIND_MAP: dict[str, SemanticTypeKind] = {
    "domain": SemanticTypeKind.SCALAR,
    "structure": SemanticTypeKind.STRUCTURE,
    "tabletype": SemanticTypeKind.TABLE_TYPE,
    "table": SemanticTypeKind.SCALAR,
    "rangetype": SemanticTypeKind.RANGE_TYPE,
    "referencetype": SemanticTypeKind.REFERENCE,
    "reference": SemanticTypeKind.REFERENCE,
    "dataelement": SemanticTypeKind.SCALAR,
}

_CDS_TYPE_KIND_MAP: dict[str, SemanticTypeKind] = {
    "structure": SemanticTypeKind.STRUCTURE,
    "builtin": SemanticTypeKind.ENUM,
    "type": SemanticTypeKind.SCALAR,
}


def semantic_type_from_ddic(type_kind: str, data_type: str = "") -> SemanticTypeKind:
    tk = type_kind.replace("_", "").lower()
    if tk in _DDIC_TYPE_KIND_MAP:
        return _DDIC_TYPE_KIND_MAP[tk]
    if data_type.upper() in ("STRU", "STRUCTURE"):
        return SemanticTypeKind.STRUCTURE
    return SemanticTypeKind.SCALAR


def semantic_type_from_cds(type_kind: str) -> SemanticTypeKind:
    return _CDS_TYPE_KIND_MAP.get(type_kind.lower(), SemanticTypeKind.SCALAR)


def semantic_type_for_type_reference(type_kind: str) -> SemanticTypeKind:
    """Semantic type of a referenced DDIC object by SAP type_kind."""
    return semantic_type_from_ddic(type_kind)
