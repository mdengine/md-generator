from __future__ import annotations

from typing import Any

import networkx as nx

from md_generator.sap.models.entities.sap_object import SapObject


def build_lineage_metadata(
    objects: list[SapObject],
    graph: nx.MultiDiGraph | None,
) -> dict[str, list[dict[str, Any]]]:
    lineage: dict[str, list[dict[str, Any]]] = {}
    for obj in objects:
        oid = obj.object_id
        entry: dict[str, Any] = {
            "object_id": oid,
            "name": obj.name,
            "kind": obj.kind.value,
            "source_path": str(obj.source_path) if obj.source_path else None,
            "upstream": [],
            "downstream": [],
        }
        if graph and oid in graph:
            for pred in graph.predecessors(oid):
                entry["upstream"].append({"id": pred, "relations": _edge_types(graph, pred, oid)})
            for succ in graph.successors(oid):
                entry["downstream"].append({"id": succ, "relations": _edge_types(graph, oid, succ)})
        lineage[oid] = [entry]
    return lineage


def _edge_types(g: nx.MultiDiGraph, u: str, v: str) -> list[str]:
    types: list[str] = []
    if g.has_edge(u, v):
        for _, data in g[u][v].items():
            types.append(data.get("relation", "LINK"))
    return types
