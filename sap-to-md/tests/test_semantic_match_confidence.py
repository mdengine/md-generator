from md_generator.sap.lineage.semantic_match import SemanticMatch


def test_semantic_match_edge_properties():
    m = SemanticMatch(confidence_score=0.82, matching_strategy="physical_name_match", match_reason="test")
    props = m.to_edge_properties()
    assert props["confidence_score"] == 0.82
    assert props["matching_strategy"] == "physical_name_match"
