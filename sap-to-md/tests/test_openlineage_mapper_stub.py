from md_generator.sap.graph.adapters.openlineage import OpenLineageMapper
from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import RelationshipType


def test_openlineage_mapper_stub():
    store = ArtifactGraphStore()
    frag = ArtifactGraph(graph_id="f")
    frag.add_node(GraphNode(node_id="ds", node_kind="dataset", label="SO_Items", namespace="HANA::"))
    frag.add_node(GraphNode(node_id="cv", node_kind="artifact", label="CV_SALES", namespace="HANA::"))
    frag.add_edge(
        GraphEdge(
            edge_id="e1",
            source_id="cv",
            target_id="ds",
            relationship=RelationshipType.READS_FROM,
        )
    )
    store.add_fragment(frag)
    ol = OpenLineageMapper(run_id="test-run")
    doc = ol.to_openlineage(store)
    assert doc["eventType"] == "COMPLETE"
    assert doc["run"]["runId"] == "test-run"
    assert len(doc["datasets"]) >= 1
