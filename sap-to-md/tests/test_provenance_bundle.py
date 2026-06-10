from md_generator.sap.canonical.provenance import ProvenanceBundle


def test_provenance_bundle_manifest():
    prov = ProvenanceBundle(
        parser_id="hana.calculation_view",
        parser_version="1.0.0",
        source_checksum="abc123",
        run_id="run-1",
    )
    d = prov.to_manifest_dict()
    assert d["parser_id"] == "hana.calculation_view"
    assert d["source_checksum"] == "abc123"
