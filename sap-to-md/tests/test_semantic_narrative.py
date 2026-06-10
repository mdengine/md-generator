from __future__ import annotations

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.graph.backends.memory import InMemoryGraphStore
from md_generator.sap.graph.model import GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.markdown.builders.renderer_context import RendererContext
from md_generator.sap.markdown.cross_link_registry import build_cross_link_registry
from md_generator.sap.markdown.semantic_narrative import format_semantic_narrative


def test_semantic_narrative_deterministic():
    store = InMemoryGraphStore(graph_id="t")
    store.add_node(GraphNode(node_id="DE1", node_kind="artifact", label="CHAR100"))
    store.add_node(GraphNode(node_id="DOM1", node_kind="artifact", label="CHAR100"))
    store.add_edge(
        GraphEdge(
            edge_id="de-dom",
            source_id="DE1",
            target_id="DOM1",
            relationship=RelationshipType.REFERENCES,
        )
    )
    art = CanonicalArtifact(
        identity=ArtifactIdentity.from_legacy(
            stable_id="DE1",
            name="CHAR100",
            namespace="DDIC::",
            semantic_entity="Identifier",
        ),
        provenance=ProvenanceBundle(parser_id="test", parser_version="1"),
        artifact_type="ddic.data_element",
        name="CHAR100",
        metadata={
            "data_element": {
                "type_kind": "domain",
                "type_name": "CHAR100",
                "long_field_label": "Character field 100",
            }
        },
    )
    cross = build_cross_link_registry(
        path_registry={
            ("DATA_ELEMENT", "CHAR100"): "ddic/data-elements/char100.md",
            ("DOMAIN", "CHAR100"): "ddic/domains/char100.md",
        },
        graph_store=store,
        artifacts=[art],
    )
    ctx = RendererContext(graph_store=store, cross_link_registry=cross)
    text = format_semantic_narrative(art, ctx)
    assert "## Semantic summary" in text
    assert "Relationship summary" in text
    assert "REFERENCES" in text
    assert "DDIC resolution chain" in text
    assert "confidence 1.00" in text
    assert "Character field 100" in text
