from md_generator.sap.chunking.spec import SemanticChunkSpec


def test_semantic_chunk_spec_jsonl():
    chunk = SemanticChunkSpec(
        chunk_id="c1",
        chunk_type="lineage_summary",
        artifact_type="hana.calculation_view",
        artifact_id="HANA::SALES::CV_SALES",
        semantic_tags=["lineage"],
        graph_refs=["e1"],
        content="Reads from SO_Items",
    )
    rec = chunk.to_jsonl_record()
    assert rec["chunk_type"] == "lineage_summary"
    assert rec["graph_refs"] == ["e1"]
