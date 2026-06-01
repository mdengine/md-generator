from __future__ import annotations

from pathlib import Path

import networkx as nx

from md_generator.sap.graph import relations as rel


def export_er_mermaid(g: nx.MultiDiGraph, path: Path, *, max_edges: int = 200) -> None:
    lines = ["erDiagram"]
    seen_edges: set[tuple[str, str, str]] = set()
    count = 0
    for u, v, key, data in g.edges(keys=True, data=True):
        if count >= max_edges:
            break
        relation = data.get("relation", "LINK")
        su = _mermaid_id(u)
        sv = _mermaid_id(v)
        pair = (su, sv, relation)
        if pair in seen_edges:
            continue
        seen_edges.add(pair)
        label = _relation_label(relation, data)
        lines.append(f"    {su} {label} {sv} : \"{relation}\"")
        count += 1
    for n, data in g.nodes(data=True):
        if data.get("kind") == "TABLE":
            nid = _mermaid_id(n)
            lines.append(f"    {nid} {{")
            lines.append(f"        string {data.get('name', 'name')}")
            lines.append("    }")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mermaid_id(node: str) -> str:
    s = node.replace(":", "_").replace(".", "_")
    return s[:40] if len(s) > 40 else s


def _relation_label(relation: str, data: dict | None = None) -> str:
    data = data or {}
    if relation == rel.NAV_PROP:
        mult = str(data.get("multiplicity", "n"))
        if mult in ("1", "0..1"):
            return "||--||"
        return "||--o{"
    if relation == rel.FK:
        return "}o--||"
    if relation in (rel.READS_TABLE, rel.ASSOCIATION):
        return "}o--o{"
    if relation == rel.COMPOSITION:
        return "||--|{"
    return "}o--o{"
