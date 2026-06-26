"""Execution path enumeration for journeys.

Traverses a JourneyIR tree and extracts distinct root-to-leaf paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR


@dataclass
class ExecutionPath:
    """Represents a single root-to-leaf path through the journey tree."""
    path_id: str
    nodes: list[str]
    labels: list[str]
    depth: int
    edge_types: list[str | None]
    conditions: list[str | None]
    has_database: bool
    has_queue: bool
    has_external_api: bool
    terminal_node_type: str


def enumerate_execution_paths(ir: JourneyIR, *, max_paths: int = 200) -> list[ExecutionPath]:
    """DFS root-to-leaf enumeration. Each leaf produces one execution path."""
    paths: list[ExecutionPath] = []
    
    def dfs(node: JourneyNodeIR, current_path: list[JourneyNodeIR]) -> None:
        if len(paths) >= max_paths:
            return
            
        new_path = current_path + [node]
        if not node.children:
            # Leaf node reached, construct path
            node_ids = [n.id for n in new_path]
            labels = [n.label for n in new_path]
            edge_types = [n.edge_relation for n in new_path]
            conditions = [n.edge_label for n in new_path]
            
            has_db = any((n.node_type or "").lower() in ("table", "collection", "database") for n in new_path)
            has_q = any((n.node_type or "").lower() in ("topic", "queue") for n in new_path)
            has_ext = any((n.node_type or "").lower() in ("external", "external_api") for n in new_path)
            
            p = ExecutionPath(
                path_id=f"path_{len(paths) + 1}",
                nodes=node_ids,
                labels=labels,
                depth=len(new_path),
                edge_types=edge_types,
                conditions=conditions,
                has_database=has_db,
                has_queue=has_q,
                has_external_api=has_ext,
                terminal_node_type=node.node_type or "unknown"
            )
            paths.append(p)
            return
            
        for child in node.children:
            dfs(child, new_path)

    if ir.root:
        dfs(ir.root, [])
        
    return paths


def write_execution_paths_markdown(paths: list[ExecutionPath], out: Path) -> None:
    """Write execution paths to a markdown file (execution-paths.md)."""
    lines = ["# Execution Paths", ""]
    for idx, p in enumerate(paths, start=1):
        lines.append(f"### Path {idx} (depth: {p.depth})")
        steps = []
        for i in range(len(p.nodes)):
            lbl = p.labels[i]
            rel = p.edge_types[i]
            cond = p.conditions[i]
            if i == 0:
                steps.append(f"`{lbl}`")
            else:
                rel_str = f" [{rel}]" if rel else ""
                cond_str = f" if ({cond})" if cond else ""
                steps.append(f" →{rel_str}{cond_str} → `{lbl}`")
        lines.append("".join(steps))
        lines.append("")
        
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
