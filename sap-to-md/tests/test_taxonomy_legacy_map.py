from md_generator.sap.graph import relations as legacy
from md_generator.sap.graph.taxonomy import RelationshipType, from_legacy, to_legacy


def test_legacy_relation_map():
    assert from_legacy(legacy.READS_TABLE) == RelationshipType.READS_FROM
    assert from_legacy(legacy.NAV_PROP) == RelationshipType.EXPOSES
    assert from_legacy(legacy.FK) == RelationshipType.REFERENCES
    assert to_legacy(RelationshipType.READS_FROM) == legacy.READS_TABLE
