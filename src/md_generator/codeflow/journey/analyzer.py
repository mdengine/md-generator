"""Journey Analyzer module.

Computes advanced journey-level analytics (longest/shortest paths, deepest call,
most called method, largest branch, circular journeys, dead journeys, unreachable nodes).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import networkx as nx

from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR
from md_generator.codeflow.journey.paths import ExecutionPath, enumerate_execution_paths
from md_generator.codeflow.journey.tree import flatten_to_list


@dataclass
class JourneyAnalysis:
    """Advanced analytics results for a single journey."""
    longest_journey: ExecutionPath | None = None
    shortest_journey: ExecutionPath | None = None
    deepest_call: JourneyNodeIR | None = None
    most_called_method: tuple[str, int] | None = None
    largest_branch: JourneyNodeIR | None = None
    largest_subtree: tuple[str, int] | None = None
    circular_journeys: list[list[str]] = None
    dead_journeys: list[str] = None
    disconnected_journeys: list[str] = None
    unused_journeys: list[str] = None


class JourneyAnalyzer:
    """Analyzes a JourneyIR instance against the source graph to extract deep insights."""

    def __init__(self, ir: JourneyIR, g: Any) -> None:
        self.ir = ir
        self.g = g

    def analyze(self) -> JourneyAnalysis:
        """Compute advanced metrics on the journey tree."""
        if not self.ir.root:
            return JourneyAnalysis()

        all_nodes = flatten_to_list(self.ir.root)
        paths = self.ir.execution_paths or enumerate_execution_paths(self.ir)
        
        # 1. Longest / shortest paths
        longest = max(paths, key=lambda p: p.depth) if paths else None
        shortest = min(paths, key=lambda p: p.depth) if paths else None
        
        # 2. Deepest call
        deepest = max(all_nodes, key=lambda n: n.depth) if all_nodes else None
        
        # 3. Most called method
        method_counts: dict[str, int] = defaultdict(int)
        method_labels: dict[str, str] = {}
        for n in all_nodes:
            if n.node_type in ("method", "function", "entry"):
                method_counts[n.id] += 1
                method_labels[n.id] = n.label
                
        most_called = None
        if method_counts:
            mc_id, mc_cnt = max(method_counts.items(), key=lambda x: x[1])
            most_called = (method_labels[mc_id], mc_cnt)
            
        # 4. Largest branch
        largest_branch = max(all_nodes, key=lambda n: len(n.children)) if all_nodes else None
        
        # 5. Largest subtree (excluding root)
        def _get_subtree_size(n: JourneyNodeIR) -> int:
            return 1 + sum(_get_subtree_size(c) for c in n.children)
            
        inner_nodes = [n for n in all_nodes if not n.is_root]
        largest_subtree = None
        if inner_nodes:
            lst_node = max(inner_nodes, key=_get_subtree_size)
            largest_subtree = (lst_node.id, _get_subtree_size(lst_node))
            
        # 6. Circular journeys
        circular_paths: list[list[str]] = []
        def _walk_cycles(node: JourneyNodeIR, path: list[str]) -> None:
            if node.is_cycle:
                if node.id in path:
                    idx = path.index(node.id)
                    circular_paths.append(path[idx:] + [node.id])
                return
            new_path = path + [node.id]
            for child in node.children:
                _walk_cycles(child, new_path)
                
        _walk_cycles(self.ir.root, [])
        
        # 7. Dead journeys (leaf application methods with no successors in graph)
        dead: list[str] = []
        for n in all_nodes:
            if n.is_leaf or not n.children:
                nt = (n.node_type or "").lower()
                if nt in ("method", "function"):
                    # check successors in original graph
                    if n.id in self.g:
                        successors = list(self.g.successors(n.id))
                        if not successors:
                            dead.append(n.label)
                            
        # 8. Unused and Disconnected journeys
        all_graph_methods = {str(node) for node, d in self.g.nodes(data=True) 
                             if (d.get("type") or d.get("kind") or "").lower() == "method"}
        visited_methods = {n.id for n in all_nodes if n.node_type in ("method", "function")}
        
        unused = sorted(list(all_graph_methods - visited_methods))
        
        disconnected: list[str] = []
        if self.ir.root.id in self.g:
            try:
                # nodes reachable from root in g
                reachable = set(nx.dfs_preorder_nodes(self.g, self.ir.root.id))
                disconnected = sorted(list(all_graph_methods - reachable))
            except Exception:
                pass
                
        return JourneyAnalysis(
            longest_journey=longest,
            shortest_journey=shortest,
            deepest_call=deepest,
            most_called_method=most_called,
            largest_branch=largest_branch,
            largest_subtree=largest_subtree,
            circular_journeys=circular_paths,
            dead_journeys=sorted(list(set(dead))),
            disconnected_journeys=disconnected,
            unused_journeys=unused,
        )


def write_journey_analysis_markdown(analysis: JourneyAnalysis, out: Path) -> None:
    """Write journey analysis report to a markdown file."""
    lines = ["# Journey Analysis Report", ""]
    
    lines.append("## Structural Insights")
    if analysis.longest_journey:
        lines.append(f"- **Longest Path:** {analysis.longest_journey.depth} steps (`{analysis.longest_journey.path_id}`)")
    if analysis.shortest_journey:
        lines.append(f"- **Shortest Path:** {analysis.shortest_journey.depth} steps (`{analysis.shortest_journey.path_id}`)")
    if analysis.deepest_call:
        lines.append(f"- **Deepest Call Node:** `{analysis.deepest_call.label}` (depth: {analysis.deepest_call.depth})")
    if analysis.most_called_method:
        lines.append(f"- **Most Repeated Call:** `{analysis.most_called_method[0]}` (appears {analysis.most_called_method[1]} times)")
    if analysis.largest_branch:
        lines.append(f"- **Largest Branching Node:** `{analysis.largest_branch.label}` (has {len(analysis.largest_branch.children)} children)")
    lines.append("")
    
    lines.append("## Cycles & Recursion")
    if analysis.circular_journeys:
        for idx, cycle in enumerate(analysis.circular_journeys, start=1):
            cycle_str = " → ".join(f"`{c}`" for c in cycle)
            lines.append(f"{idx}. {cycle_str}")
    else:
        lines.append("*No circular paths or cycles detected.*")
    lines.append("")
    
    lines.append("## Dead-end Methods")
    lines.append("Methods that are leaves in the journey and have no outgoing calls in the code:")
    if analysis.dead_journeys:
        for d in analysis.dead_journeys[:30]:
            lines.append(f"- `{d}`")
        if len(analysis.dead_journeys) > 30:
            lines.append(f"- *...and {len(analysis.dead_journeys) - 30} more.*")
    else:
        lines.append("- *None detected.*")
    lines.append("")

    lines.append("## Unreachable Methods")
    lines.append("Methods in the codebase that cannot be reached from this journey's root:")
    if analysis.disconnected_journeys:
        for d in analysis.disconnected_journeys[:20]:
            lines.append(f"- `{d}`")
        if len(analysis.disconnected_journeys) > 20:
            lines.append(f"- *...and {len(analysis.disconnected_journeys) - 20} more.*")
    else:
        lines.append("- *All methods reachable from root.*")
    lines.append("")
    
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
