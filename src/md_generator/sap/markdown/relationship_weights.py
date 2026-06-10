from __future__ import annotations

from md_generator.sap.graph.taxonomy import RelationshipType

RELATIONSHIP_WEIGHT: dict[RelationshipType, float] = {
    RelationshipType.REFERENCES: 1.0,
    RelationshipType.CONTAINS: 1.0,
    RelationshipType.READS_FROM: 0.7,
    RelationshipType.WRITES_TO: 0.65,
    RelationshipType.SAME_AS: 0.6,
    RelationshipType.EQUIVALENT_TO: 0.6,
    RelationshipType.EXPOSES: 0.65,
    RelationshipType.SERVES: 0.65,
    RelationshipType.DEPENDS_ON: 0.55,
    RelationshipType.CALLS: 0.5,
    RelationshipType.INCLUDES: 0.5,
    RelationshipType.TRANSFORMS: 0.45,
    RelationshipType.JOINS: 0.45,
    RelationshipType.DERIVES_FROM: 0.45,
    RelationshipType.FILTERS: 0.4,
    RelationshipType.AGGREGATES: 0.4,
    RelationshipType.UNIONS: 0.4,
    RelationshipType.MAPS_TO: 0.4,
}


def relationship_weight(rel: RelationshipType) -> float:
    return RELATIONSHIP_WEIGHT.get(rel, 0.3)
