from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import RelationshipType


def test_store_merge_and_traversal():
    store = ArtifactGraphStore()
    f1 = ArtifactGraph(graph_id="f1")
    f1.add_node(GraphNode(node_id="cv", label="CV_SALES"))
    f1.add_node(GraphNode(node_id="tbl", label="SO_Items", node_kind="dataset"))
    f1.add_edge(
        GraphEdge(
            edge_id="e1",
            source_id="cv",
            target_id="tbl",
            relationship=RelationshipType.READS_FROM,
        )
    )
    f2 = ArtifactGraph(graph_id="f2")
    f2.add_node(GraphNode(node_id="cds", label="ZI_SALES"))
    f2.add_edge(
        GraphEdge(
            edge_id="e2",
            source_id="cds",
            target_id="cv",
            relationship=RelationshipType.DERIVES_FROM,
        )
    )
    store.add_fragment(f1)
    store.add_fragment(f2)
    assert len(store.graph.nodes) == 3
    upstream = store.upstream("cv", relationship_types={RelationshipType.DERIVES_FROM})
    assert "cds" in upstream
    downstream = store.downstream("cv", relationship_types={RelationshipType.READS_FROM})
    assert "tbl" in downstream
