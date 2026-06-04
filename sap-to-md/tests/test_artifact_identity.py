from md_generator.sap.canonical.identity import ArtifactIdentity


def test_artifact_identity_from_legacy():
    ident = ArtifactIdentity.from_legacy(
        stable_id="CDS::ZI_SALES",
        name="ZI_SALES",
        namespace="CDS::",
        semantic_entity="entity:sales_order",
        aliases=["CV_SALES"],
    )
    assert ident.stable_id == "CDS::ZI_SALES"
    assert ident.semantic_id == "entity:sales_order"
    assert "CV_SALES" in ident.aliases
