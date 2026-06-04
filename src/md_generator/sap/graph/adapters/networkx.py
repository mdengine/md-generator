from __future__ import annotations

import networkx as nx

from md_generator.sap.graph.model import ArtifactGraph
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import from_legacy, to_legacy


def artifact_graph_to_networkx(graph: ArtifactGraph) -> nx.MultiDiGraph:
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    for node in graph.nodes.values():
        g.add_node(
            node.node_id,
            kind=node.node_kind,
            name=node.label or node.node_id,
            namespace=node.namespace,
            artifact_type=node.artifact_type,
            **node.properties,
        )
    for edge in graph.edges.values():
        g.add_edge(
            edge.source_id,
            edge.target_id,
            relation=to_legacy(edge.relationship),
            relationship=edge.relationship.value,
            **edge.properties,
        )
    return g


def networkx_to_artifact_graph(g: nx.MultiDiGraph, graph_id: str = "legacy") -> ArtifactGraph:
    graph = ArtifactGraph(graph_id=graph_id)
    for nid, data in g.nodes(data=True):
        props = {k: v for k, v in data.items() if k not in ("kind", "name", "namespace", "artifact_type")}
        from md_generator.sap.graph.model import GraphNode

        graph.add_node(
            GraphNode(
                node_id=str(nid),
                node_kind=str(data.get("kind", "artifact")),
                label=str(data.get("name", nid)),
                namespace=str(data.get("namespace", "")),
                artifact_type=data.get("artifact_type"),
                properties=props,
            )
        )
    for u, v, key, data in g.edges(keys=True, data=True):
        from md_generator.sap.graph.model import GraphEdge

        rel = data.get("relation") or data.get("relationship", "DEPENDS_ON")
        edge_id = f"{u}->{v}:{key}"
        props = {k: v for k, v in data.items() if k not in ("relation", "relationship")}
        graph.add_edge(
            GraphEdge(
                edge_id=edge_id,
                source_id=str(u),
                target_id=str(v),
                relationship=from_legacy(str(rel)),
                properties=props,
            )
        )
    return graph


def store_from_networkx(g: nx.MultiDiGraph) -> ArtifactGraphStore:
    store = ArtifactGraphStore()
    store.add_fragment(networkx_to_artifact_graph(g))
    return store
