from __future__ import annotations

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.graph.backends.memory import InMemoryGraphStore
from md_generator.sap.graph.model import GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.markdown.cross_link_registry import build_cross_link_registry
from md_generator.sap.markdown.relationship_weights import relationship_weight


def _artifact(name: str, artifact_type: str) -> CanonicalArtifact:
    return CanonicalArtifact(
        identity=ArtifactIdentity.from_legacy(
            stable_id=f"DDIC::{artifact_type}::{name}",
            name=name,
            namespace="DDIC::",
        ),
        provenance=ProvenanceBundle(parser_id="test", parser_version="1"),
        artifact_type=artifact_type,
        name=name,
        metadata={},
    )


def test_resolve_link_path_registry():
    reg = build_cross_link_registry(
        path_registry={("DOMAIN", "CHAR100"): "ddic/domains/char100.md"},
        artifacts=[_artifact("CHAR100", "ddic.domain")],
    )
    link = reg.resolve_link("DOMAIN", "CHAR100")
    assert link.href == "ddic/domains/char100.md"
    assert link.confidence == 1.0
    assert link.strategy == "path_registry"


def test_resolve_type_reference_falls_back_to_domain():
    reg = build_cross_link_registry(
        path_registry={("DOMAIN", "CHAR100"): "ddic/domains/char100.md"},
    )
    link = reg.resolve_type_reference("domain", "CHAR100")
    assert link.href == "ddic/domains/char100.md"


def test_neighbors_sorted_by_weight():
    store = InMemoryGraphStore(graph_id="t")
    store.add_node(GraphNode(node_id="A", node_kind="artifact", label="A"))
    store.add_node(GraphNode(node_id="B", node_kind="artifact", label="B"))
    store.add_node(GraphNode(node_id="C", node_kind="artifact", label="C"))
    store.add_edge(
        GraphEdge(
            edge_id="a-b",
            source_id="A",
            target_id="B",
            relationship=RelationshipType.READS_FROM,
        )
    )
    store.add_edge(
        GraphEdge(
            edge_id="a-c",
            source_id="A",
            target_id="C",
            relationship=RelationshipType.REFERENCES,
        )
    )
    reg = build_cross_link_registry(path_registry={}, graph_store=store)
    neighbors = reg.neighbors_for_render("A")
    assert neighbors[0][1].relationship == RelationshipType.REFERENCES
    assert relationship_weight(neighbors[0][1].relationship) >= relationship_weight(
        neighbors[1][1].relationship
    )


def test_related_ddic_chain():
    art = _artifact("CHAR100", "ddic.data_element")
    art.metadata["data_element"] = {
        "type_kind": "domain",
        "type_name": "CHAR100",
    }
    reg = build_cross_link_registry(
        path_registry={
            ("DATA_ELEMENT", "CHAR100"): "ddic/data-elements/char100.md",
            ("DOMAIN", "CHAR100"): "ddic/domains/char100.md",
        },
        artifacts=[art],
    )
    chain = reg.related_ddic_chain("CHAR100")
    assert len(chain) == 2
    assert chain[0].strategy == "path_registry"
    assert chain[1].href == "ddic/domains/char100.md"
