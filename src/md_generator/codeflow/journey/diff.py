"""Journey diffing module.

Compares two JourneyIR instances to identify structural, edge, path, and integration changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR, JourneyEdgeIR
from md_generator.codeflow.journey.paths import ExecutionPath, enumerate_execution_paths
from md_generator.codeflow.journey.tree import flatten_to_list


@dataclass
class PathDiff:
    """Represents a diff of a single execution path."""
    path_id: str
    status: str  # "added" | "removed" | "modified"
    base_path: ExecutionPath | None = None
    head_path: ExecutionPath | None = None
    changes: list[str] = field(default_factory=list)


@dataclass
class JourneyDiff:
    """The result of comparing a base journey against a head journey."""
    base_commit: str
    head_commit: str
    added_nodes: list[dict[str, Any]] = field(default_factory=list)
    removed_nodes: list[dict[str, Any]] = field(default_factory=list)
    added_edges: list[dict[str, Any]] = field(default_factory=list)
    removed_edges: list[dict[str, Any]] = field(default_factory=list)
    changed_paths: list[PathDiff] = field(default_factory=list)
    new_external_dependencies: list[str] = field(default_factory=list)
    removed_external_dependencies: list[str] = field(default_factory=list)
    new_databases: list[str] = field(default_factory=list)
    removed_databases: list[str] = field(default_factory=list)
    new_queues: list[str] = field(default_factory=list)
    removed_queues: list[str] = field(default_factory=list)
    depth_change: int = 0
    node_count_change: int = 0


def compute_journey_diff(
    base_ir: JourneyIR,
    head_ir: JourneyIR,
    base_commit: str,
    head_commit: str,
) -> JourneyDiff:
    """Compute the difference between base and head JourneyIR instances."""
    base_nodes = flatten_to_list(base_ir.root) if base_ir.root else []
    head_nodes = flatten_to_list(head_ir.root) if head_ir.root else []
    
    base_node_map = {n.id: n for n in base_nodes}
    head_node_map = {n.id: n for n in head_nodes}
    
    # 1. Nodes added/removed
    added_node_ids = set(head_node_map.keys()) - set(base_node_map.keys())
    removed_node_ids = set(base_node_map.keys()) - set(head_node_map.keys())
    
    added_nodes = [{"id": nid, "label": head_node_map[nid].label, "type": head_node_map[nid].node_type} for nid in sorted(added_node_ids)]
    removed_nodes = [{"id": nid, "label": base_node_map[nid].label, "type": base_node_map[nid].node_type} for nid in sorted(removed_node_ids)]
    
    # 2. Edges added/removed
    base_edge_set = {(e.source_id, e.target_id, e.relation) for e in base_ir.edges}
    head_edge_set = {(e.source_id, e.target_id, e.relation) for e in head_ir.edges}
    
    added_edges_raw = head_edge_set - base_edge_set
    removed_edges_raw = base_edge_set - head_edge_set
    
    added_edges = [{"source_id": e[0], "target_id": e[1], "relation": e[2]} for e in sorted(added_edges_raw)]
    removed_edges = [{"source_id": e[0], "target_id": e[1], "relation": e[2]} for e in sorted(removed_edges_raw)]
    
    # 3. Integration point additions/removals
    base_db = {n.label for n in base_nodes if (n.node_type or "").lower() in ("table", "collection", "database")}
    head_db = {n.label for n in head_nodes if (n.node_type or "").lower() in ("table", "collection", "database")}
    new_db = sorted(list(head_db - base_db))
    rem_db = sorted(list(base_db - head_db))
    
    base_q = {n.label for n in base_nodes if (n.node_type or "").lower() in ("topic", "queue")}
    head_q = {n.label for n in head_nodes if (n.node_type or "").lower() in ("topic", "queue")}
    new_q = sorted(list(head_q - base_q))
    rem_q = sorted(list(base_q - head_q))
    
    base_ext = {n.label for n in base_nodes if (n.node_type or "").lower() in ("external", "external_api")}
    head_ext = {n.label for n in head_nodes if (n.node_type or "").lower() in ("external", "external_api")}
    new_ext = sorted(list(head_ext - base_ext))
    rem_ext = sorted(list(base_ext - head_ext))
    
    # 4. Compare execution paths
    base_paths = base_ir.execution_paths or enumerate_execution_paths(base_ir)
    head_paths = head_ir.execution_paths or enumerate_execution_paths(head_ir)
    
    base_by_seq = {tuple(p.nodes): p for p in base_paths}
    head_by_seq = {tuple(p.nodes): p for p in head_paths}
    
    added_seqs = set(head_by_seq.keys()) - set(base_by_seq.keys())
    removed_seqs = set(base_by_seq.keys()) - set(head_by_seq.keys())
    
    changed_paths: list[PathDiff] = []
    paired_added = set()
    paired_removed = set()
    
    # Pair modified paths
    for r_seq in removed_seqs:
        bp = base_by_seq[r_seq]
        for a_seq in added_seqs:
            if a_seq in paired_added:
                continue
            ap = head_by_seq[a_seq]
            if bp.nodes[0] == ap.nodes[0] and bp.nodes[-1] == ap.nodes[-1]:
                # Path start/leaf match, nodes changed -> modified
                changes = []
                added_mid = set(ap.nodes) - set(bp.nodes)
                removed_mid = set(bp.nodes) - set(ap.nodes)
                if added_mid:
                    changes.append(f"Added calls: {', '.join(head_node_map[nid].label if nid in head_node_map else nid for nid in added_mid)}")
                if removed_mid:
                    changes.append(f"Removed calls: {', '.join(base_node_map[nid].label if nid in base_node_map else nid for nid in removed_mid)}")
                
                changed_paths.append(PathDiff(
                    path_id=ap.path_id,
                    status="modified",
                    base_path=bp,
                    head_path=ap,
                    changes=changes
                ))
                paired_added.add(a_seq)
                paired_removed.add(r_seq)
                break
                
    for a_seq in added_seqs - paired_added:
        ap = head_by_seq[a_seq]
        changed_paths.append(PathDiff(
            path_id=ap.path_id,
            status="added",
            base_path=None,
            head_path=ap,
            changes=["New execution path introduced."]
        ))
        
    for r_seq in removed_seqs - paired_removed:
        bp = base_by_seq[r_seq]
        changed_paths.append(PathDiff(
            path_id=bp.path_id,
            status="removed",
            base_path=bp,
            head_path=None,
            changes=["Execution path removed."]
        ))
        
    return JourneyDiff(
        base_commit=base_commit,
        head_commit=head_commit,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
        changed_paths=changed_paths,
        new_external_dependencies=new_ext,
        removed_external_dependencies=rem_ext,
        new_databases=new_db,
        removed_databases=rem_db,
        new_queues=new_q,
        removed_queues=rem_q,
        depth_change=head_ir.statistics.maximum_depth - base_ir.statistics.maximum_depth,
        node_count_change=head_ir.statistics.node_count - base_ir.statistics.node_count,
    )


def write_journey_diff_markdown(diff: JourneyDiff, out: Path) -> None:
    """Write journey diff report in markdown format (journey-diff.md)."""
    lines = [
        f"# Journey Diff: {diff.base_commit[:7]} → {diff.head_commit[:7]}",
        "",
        "## Summary",
        "| Metric | Base | Head | Change |",
        "|--------|------|------|--------|",
        f"| Total Nodes | {len(diff.removed_nodes)} | {len(diff.added_nodes)} | {'+' if diff.node_count_change >= 0 else ''}{diff.node_count_change} |",
        f"| Max Depth Change | - | - | {'+' if diff.depth_change >= 0 else ''}{diff.depth_change} |",
        "",
    ]
    
    if diff.added_nodes:
        lines.append("## Added Calls")
        for n in diff.added_nodes:
            lines.append(f"- `{n['label']}` ({n['type']})")
        lines.append("")
        
    if diff.removed_nodes:
        lines.append("## Removed Calls")
        for n in diff.removed_nodes:
            lines.append(f"- `{n['label']}` ({n['type']})")
        lines.append("")
        
    if diff.changed_paths:
        lines.append("## Changed Execution Paths")
        for p in diff.changed_paths:
            lines.append(f"### Path `{p.path_id}` ({p.status.upper()})")
            for c in p.changes:
                lines.append(f"- {c}")
            lines.append("")
            
    if diff.new_external_dependencies:
        lines.append("## New External Dependencies")
        for e in diff.new_external_dependencies:
            lines.append(f"- `{e}`")
        lines.append("")
        
    if diff.new_databases:
        lines.append("## New Databases")
        for db in diff.new_databases:
            lines.append(f"- `{db}`")
        lines.append("")
        
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
