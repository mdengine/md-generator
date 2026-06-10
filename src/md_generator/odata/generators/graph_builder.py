from __future__ import annotations

import networkx as nx

from md_generator.odata.generators import relations as rel
from md_generator.odata.models.domain import ODataMetadataDocument


def build_odata_graph(documents: list[ODataMetadataDocument]) -> nx.MultiDiGraph:
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    entity_nodes: dict[tuple[str, str], str] = {}

    for doc in documents:
        svc_id = doc.stable_id or f"service:{doc.service_name}"
        g.add_node(svc_id, kind="ODATA_SERVICE", name=doc.service_name)
        for entity in doc.entity_types:
            et_id = entity.stable_id or f"{doc.service_name}:{entity.name}"
            entity_nodes[(doc.service_name, entity.name.upper())] = et_id
            g.add_node(et_id, kind="ODATA_ENTITY", name=entity.name)
        for es in doc.entity_sets:
            es_id = es.stable_id or f"{doc.service_name}:{es.name}"
            g.add_node(es_id, kind="ODATA_ENTITY_SET", name=es.name)
            g.add_edge(svc_id, es_id, relation=rel.ODATA_SERVICE)
            et_key = (doc.service_name, es.entity_type.upper())
            et_id = entity_nodes.get(et_key)
            if et_id:
                g.add_edge(es_id, et_id, relation=rel.ODATA_ENTITY_SET)
        for entity in doc.entity_types:
            et_id = entity_nodes[(doc.service_name, entity.name.upper())]
            for nav in entity.navigation_properties:
                tgt_key = (doc.service_name, nav.target_type.upper())
                tgt_id = entity_nodes.get(tgt_key)
                if not tgt_id:
                    tgt_id = f"{doc.service_name}:{nav.target_type}"
                    g.add_node(tgt_id, kind="ODATA_ENTITY", name=nav.target_type)
                g.add_edge(
                    et_id,
                    tgt_id,
                    relation=rel.NAV_PROP,
                    name=nav.name,
                    multiplicity=nav.multiplicity,
                )
        for action in doc.actions:
            a_id = action.stable_id or f"{doc.service_name}:{action.name}"
            g.add_node(a_id, kind="ODATA_ACTION", name=action.name)
            g.add_edge(svc_id, a_id, relation=rel.ODATA_ACTION)

    return g


def export_graph_json(g: nx.MultiDiGraph, path) -> None:
    import json
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "nodes": [{"id": n, **d} for n, d in g.nodes(data=True)],
        "edges": [
            {"source": u, "target": v, "key": k, **d}
            for u, v, k, d in g.edges(keys=True, data=True)
        ],
    }
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
