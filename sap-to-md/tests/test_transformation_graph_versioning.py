from md_generator.sap.canonical.transformation.graph import TransformationGraph


def test_transformation_graph_version_fields():
    tg = TransformationGraph(graph_id="tg1", execution_semantic="hana_cv")
    assert tg.graph_version == "1.0.0"
    assert tg.graph_schema_version == "1.0.0"
    assert tg.execution_semantic == "hana_cv"
