from __future__ import annotations

from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.models.metadata.ddic_kinds import DdicObjectKind, ddic_kind_from_type_kind


def _target_node_id(kind: DdicObjectKind, name: str) -> str:
    return f"DDIC::{kind}::{name.upper()}"


def wire_type_reference(
    graph: ArtifactGraph,
    source_id: str,
    type_kind: str,
    type_name: str,
    *,
    resolved_object_id: str = "",
) -> None:
    target = type_name.upper()
    if not target:
        return
    ddic_kind = ddic_kind_from_type_kind(type_kind)
    if ddic_kind is None:
        return
    tid = resolved_object_id or _target_node_id(ddic_kind, target)
    graph.add_node(
        GraphNode(node_id=tid, node_kind="artifact", label=target, namespace="DDIC::"),
    )
    graph.add_edge(
        GraphEdge(
            edge_id=f"{source_id}->refs->{tid}",
            source_id=source_id,
            target_id=tid,
            relationship=RelationshipType.REFERENCES,
            properties={"reference_type": type_kind, "ddic_object_kind": ddic_kind},
        )
    )


def wire_components(
    graph: ArtifactGraph,
    source_id: str,
    components: list[dict],
    *,
    edge_relationship: RelationshipType = RelationshipType.CONTAINS,
) -> None:
    seen: set[str] = set()
    for comp in components:
        de = (comp.get("data_element") or comp.get("type_name") or "").upper()
        cname = comp.get("name", "")
        if de and de not in seen:
            seen.add(de)
            tid = f"DDIC::TYPE::{de}"
            graph.add_node(GraphNode(node_id=tid, node_kind="artifact", label=de, namespace="DDIC::"))
            graph.add_edge(
                GraphEdge(
                    edge_id=f"{source_id}->{edge_relationship.value.lower()}->{tid}:{cname}",
                    source_id=source_id,
                    target_id=tid,
                    relationship=edge_relationship,
                    properties={"component": cname},
                )
            )
