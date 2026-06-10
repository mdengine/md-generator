from __future__ import annotations

import pytest

from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType


def test_graph_node_edge_roundtrip():
    graph = ArtifactGraph(graph_id="test")
    graph.add_node(GraphNode(node_id="a", label="A", namespace="HANA::"))
    graph.add_edge(
        GraphEdge(
            edge_id="e1",
            source_id="a",
            target_id="b",
            relationship=RelationshipType.READS_FROM,
        )
    )
    assert "a" in graph.nodes
    assert graph.edges["e1"].relationship == RelationshipType.READS_FROM


def test_artifact_graph_merge():
    g1 = ArtifactGraph(graph_id="g1")
    g1.add_node(GraphNode(node_id="x", label="X"))
    g2 = ArtifactGraph(graph_id="g2")
    g2.add_node(GraphNode(node_id="x", label="X2", properties={"v": 1}))
    g2.add_node(GraphNode(node_id="y", label="Y"))
    g1.merge(g2)
    assert len(g1.nodes) == 2
    assert g1.nodes["x"].properties.get("v") == 1
