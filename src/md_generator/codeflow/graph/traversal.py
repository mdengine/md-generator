from __future__ import annotations

import networkx as nx


class GraphTraversal:
    @staticmethod
    def bfs(g: nx.MultiDiGraph, start: str, max_depth: int | None = None) -> list[str]:
        """Cycle-safe and depth-limited BFS traversal."""
        if start not in g:
            return []
        visited = {start}
        queue = [(start, 0)]
        result = []
        while queue:
            node, depth = queue.pop(0)
            result.append(node)
            if max_depth is not None and depth >= max_depth:
                continue
            for neighbor in g.successors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return result

    @staticmethod
    def dfs(g: nx.MultiDiGraph, start: str, max_depth: int | None = None) -> list[str]:
        """Cycle-safe and depth-limited DFS traversal."""
        if start not in g:
            return []
        visited = set()
        result = []

        def walk(node: str, depth: int) -> None:
            visited.add(node)
            result.append(node)
            if max_depth is not None and depth >= max_depth:
                return
            for neighbor in g.successors(node):
                if neighbor not in visited:
                    walk(neighbor, depth + 1)

        walk(start, 0)
        return result

    @staticmethod
    def shortest_path(g: nx.MultiDiGraph, source: str, target: str) -> list[str] | None:
        """Finds the shortest path between source and target, returns None if unreachable."""
        if source not in g or target not in g:
            return None
        try:
            return list(nx.shortest_path(g, source=source, target=target))
        except (nx.NetworkXNoPath, KeyError):
            return None

    @staticmethod
    def all_paths(g: nx.MultiDiGraph, source: str, target: str, cutoff: int | None = None) -> list[list[str]]:
        """Finds all paths from source to target with depth cutoff."""
        if source not in g or target not in g:
            return []
        try:
            # MultiDiGraph requires converting to DiGraph for standard path walks or handles directly
            dg = nx.DiGraph(g)
            return list(nx.all_simple_paths(dg, source=source, target=target, cutoff=cutoff))
        except (nx.NetworkXNoPath, KeyError, ValueError):
            return []

    @staticmethod
    def reverse_traversal(g: nx.MultiDiGraph, start: str, max_depth: int | None = None) -> list[str]:
        """Cycle-safe BFS reverse (ancestors) traversal."""
        if start not in g:
            return []
        visited = {start}
        queue = [(start, 0)]
        result = []
        while queue:
            node, depth = queue.pop(0)
            result.append(node)
            if max_depth is not None and depth >= max_depth:
                continue
            for predecessor in g.predecessors(node):
                if predecessor not in visited:
                    visited.add(predecessor)
                    queue.append((predecessor, depth + 1))
        return result

    @staticmethod
    def detect_cycles(g: nx.MultiDiGraph) -> list[list[str]]:
        """Returns lists of nodes involved in simple cycles."""
        dg = nx.DiGraph(g)
        try:
            return list(nx.simple_cycles(dg))
        except Exception:
            return []

    @staticmethod
    def strongly_connected_components(g: nx.MultiDiGraph) -> list[set[str]]:
        """Finds strongly connected components."""
        dg = nx.DiGraph(g)
        try:
            return list(nx.strongly_connected_components(dg))
        except Exception:
            return []

    @classmethod
    def impact_analysis(cls, g: nx.MultiDiGraph, start: str, depth: int = 5) -> list[str]:
        """Finds all downstream nodes impacted by a change at start node."""
        return cls.bfs(g, start, max_depth=depth)[1:]  # Exclude start node itself

    @classmethod
    def dependency_traversal(cls, g: nx.MultiDiGraph, start: str, depth: int = 5) -> list[str]:
        """Finds all upstream configurations and modules this node depends on."""
        return cls.reverse_traversal(g, start, max_depth=depth)[1:]
