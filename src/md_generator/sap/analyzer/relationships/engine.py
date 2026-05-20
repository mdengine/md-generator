from __future__ import annotations

from typing import Any

import networkx as nx

from md_generator.sap.models.entities.sap_object import SapObject


def summarize_relationships(
    graph: nx.MultiDiGraph,
    objects: list[SapObject],
    *,
    cap: int = 80,
) -> dict[str, list[dict[str, Any]]]:
    by_id = {o.object_id: o for o in objects}
    out: dict[str, list[dict[str, Any]]] = {}
    for obj in objects:
        oid = obj.object_id
        rels: list[dict[str, Any]] = []
        if oid not in graph:
            out[oid] = rels
            continue
        for _, tgt, data in graph.out_edges(oid, data=True):
            rels.append(
                {
                    "target_id": tgt,
                    "target_name": by_id[tgt].name if tgt in by_id else tgt,
                    "relation": data.get("relation", "LINK"),
                }
            )
            if len(rels) >= cap:
                break
        out[oid] = rels
    return out
