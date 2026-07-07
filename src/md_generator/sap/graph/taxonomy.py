from __future__ import annotations

from enum import Enum

from md_generator.sap.graph import relations as legacy


class RelationshipType(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    READS_FROM = "READS_FROM"
    WRITES_TO = "WRITES_TO"
    TRANSFORMS = "TRANSFORMS"
    FILTERS = "FILTERS"
    AGGREGATES = "AGGREGATES"
    JOINS = "JOINS"
    UNIONS = "UNIONS"
    DERIVES_FROM = "DERIVES_FROM"
    MAPS_TO = "MAPS_TO"
    EXPOSES = "EXPOSES"
    SERVES = "SERVES"
    CALLS = "CALLS"
    EXECUTES = "EXECUTES"
    INCLUDES = "INCLUDES"
    SAME_AS = "SAME_AS"
    EQUIVALENT_TO = "EQUIVALENT_TO"


LEGACY_RELATION_MAP: dict[str, RelationshipType] = {
    legacy.FK: RelationshipType.REFERENCES,
    legacy.READS_TABLE: RelationshipType.READS_FROM,
    legacy.WRITES_TABLE: RelationshipType.WRITES_TO,
    legacy.CALLS: RelationshipType.CALLS,
    legacy.INCLUDES: RelationshipType.INCLUDES,
    legacy.ASSOCIATION: RelationshipType.EXPOSES,
    legacy.COMPOSITION: RelationshipType.CONTAINS,
    legacy.MASTER_TX: RelationshipType.DEPENDS_ON,
    legacy.CROSS_PACKAGE: RelationshipType.DEPENDS_ON,
    legacy.ODATA_ENTITY_SET: RelationshipType.SERVES,
    legacy.ODATA_ACTION: RelationshipType.EXPOSES,
    legacy.NAV_PROP: RelationshipType.EXPOSES,
}


def from_legacy(relation: str) -> RelationshipType:
    if relation in LEGACY_RELATION_MAP:
        return LEGACY_RELATION_MAP[relation]
    try:
        return RelationshipType(relation)
    except ValueError:
        return RelationshipType.DEPENDS_ON


def to_legacy(relationship: RelationshipType) -> str:
    for legacy_key, mapped in LEGACY_RELATION_MAP.items():
        if mapped == relationship:
            return legacy_key
    return relationship.value
