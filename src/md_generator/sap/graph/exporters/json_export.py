from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph


def export_graph_json(g: nx.MultiDiGraph, path: Path) -> None:
    data = json_graph.node_link_data(g, edges="links")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
