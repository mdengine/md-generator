from md_generator.sap.graph.taxonomy import RelationshipType


def test_relationship_type_values():
    assert RelationshipType.READS_FROM.value == "READS_FROM"
    assert RelationshipType.SAME_AS.value == "SAME_AS"
