from __future__ import annotations

from typing import Any

import networkx as nx

from md_generator.codeflow.graph.traversal import GraphTraversal


class GraphQuery:
    def __init__(self, g: nx.MultiDiGraph) -> None:
        self.g = g

    def find_nodes_by_kind(self, kind: str) -> list[dict[str, Any]]:
        res = []
        for n, d in self.g.nodes(data=True):
            if d.get("kind") == kind or d.get("type") == kind.lower():
                res.append({"id": n, **d})
        return res

    def find_methods(self) -> list[dict[str, Any]]:
        return self.find_nodes_by_kind("METHOD")

    def find_tables(self) -> list[dict[str, Any]]:
        return self.find_nodes_by_kind("TABLE")

    def find_dependencies(self) -> list[dict[str, Any]]:
        return self.find_nodes_by_kind("DEPENDENCY")

    def find_config(self) -> list[dict[str, Any]]:
        return self.find_nodes_by_kind("CONFIG")

    def find_resources(self) -> list[dict[str, Any]]:
        return self.find_nodes_by_kind("RESOURCE")

    def find_callers(self, node_id: str) -> list[dict[str, Any]]:
        if node_id not in self.g:
            return []
        res = []
        for pred in self.g.predecessors(node_id):
            res.append({"id": pred, **self.g.nodes[pred]})
        return res

    def find_callees(self, node_id: str) -> list[dict[str, Any]]:
        if node_id not in self.g:
            return []
        res = []
        for succ in self.g.successors(node_id):
            res.append({"id": succ, **self.g.nodes[succ]})
        return res

    def find_paths(self, source_id: str, target_id: str, cutoff: int | None = None) -> list[list[str]]:
        return GraphTraversal.all_paths(self.g, source_id, target_id, cutoff)

    def find_impacts(self, node_id: str, depth: int = 5) -> list[str]:
        return GraphTraversal.impact_analysis(self.g, node_id, depth)
