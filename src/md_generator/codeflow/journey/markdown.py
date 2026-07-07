"""Markdown rendering for journeys.

Renders JourneyIR and JourneyForest to markdown files.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR, JourneyNodeIR
from md_generator.codeflow.journey.formatter import format_tree_lines
from md_generator.codeflow.journey.tree import flatten_to_list


def journey_to_markdown(ir: JourneyIR) -> str:
    """Render a JourneyIR instance to a markdown string."""
    cfg = ir.metadata.config
    stats = ir.statistics
    
    # Flatten the tree to extract items
    all_nodes = flatten_to_list(ir.root)
    
    # Extract databases, queues, externals, configs, frameworks
    databases = sorted({n.label for n in all_nodes if (n.node_type or "").lower() in ("table", "collection", "database")})
    queues = sorted({n.label for n in all_nodes if (n.node_type or "").lower() in ("topic", "queue")})
    externals = sorted({n.label for n in all_nodes if (n.node_type or "").lower() in ("external", "external_api")})
    configs = sorted({n.label for n in all_nodes if (n.node_type or "").lower() in ("config", "configuration")})
    frameworks = sorted({n.framework for n in all_nodes if n.framework})
    
    lines = []
    
    # 1. Journey Summary
    lines.append(f"# Journey: {ir.metadata.entry_label}")
    lines.append("")
    lines.append(f"- **Journey Type:** {ir.metadata.journey_type.value}")
    lines.append(f"- **Entry Point:** `{ir.metadata.entry_id}`")
    lines.append(f"- **Total Depth:** {stats.maximum_depth}")
    lines.append(f"- **Total Nodes:** {stats.node_count}")
    lines.append(f"- **Truncated:** {'Yes' if ir.metadata.truncated else 'No'}")
    lines.append("")
    
    # 2. Entry Point Details
    lines.append("## Entry Point Details")
    lines.append(f"- **Symbol:** `{ir.metadata.entry_id}`")
    if ir.root.file_path:
        lines.append(f"- **File:** `{ir.root.file_path}`")
    if ir.root.framework:
        lines.append(f"- **Framework:** `{ir.root.framework}`")
    if ir.root.language:
        lines.append(f"- **Language:** `{ir.root.language}`")
    lines.append("")
    
    # 3. Execution Journey (Indented Tree)
    lines.append("## Execution Journey")
    lines.append("```text")
    tree_lines = format_tree_lines(
        ir.root,
        show_language=True,
        show_edge=True,
        show_stop=True,
        show_cfg=cfg.include_cfg,
    )
    lines.extend(tree_lines)
    lines.append("```")
    lines.append("")
    
    # 4. Traversal Metrics
    lines.append("## Traversal Metrics")
    lines.append(f"- **Max Depth:** {stats.maximum_depth}")
    lines.append(f"- **Average Depth:** {stats.average_depth:.2f}")
    lines.append(f"- **Visited Nodes:** {stats.node_count}")
    lines.append(f"- **Visited Edges:** {stats.edge_count}")
    lines.append("")
    
    # 5. Cycles & Recursion
    lines.append("## Cycles & Recursion")
    lines.append(f"- **Recursion Count:** {stats.recursion_count}")
    lines.append(f"- **Cycle Count:** {stats.cycle_count}")
    if ir.metadata.cycle_nodes:
        lines.append("")
        lines.append("### Cycle Nodes")
        for node_id in sorted(ir.metadata.cycle_nodes):
            lines.append(f"- `{node_id}`")
    lines.append("")
    
    # 6. Integration Points
    lines.append("## Integration Points")
    lines.append(f"- **External API Calls:** {stats.external_api_count}")
    lines.append(f"- **Database Tables Referenced:** {stats.database_count}")
    lines.append(f"- **Queues/Topics Interacted:** {stats.queue_count}")
    
    if databases:
        lines.append("")
        lines.append("### Database Tables")
        for db in databases:
            lines.append(f"- `{db}`")
            
    if queues:
        lines.append("")
        lines.append("### Queues & Topics")
        for q in queues:
            lines.append(f"- `{q}`")
            
    if externals:
        lines.append("")
        lines.append("### External APIs")
        for ext in externals:
            lines.append(f"- `{ext}`")
    lines.append("")
    
    # 7. Frameworks & Configuration
    lines.append("## Frameworks & Configuration")
    if frameworks:
        lines.append("- **Frameworks Detected:** " + ", ".join(f"`{fw}`" for fw in frameworks))
    else:
        lines.append("- **Frameworks Detected:** None")
        
    if configs:
        lines.append("- **Configuration Keys:**")
        for c in configs:
            lines.append(f"  - `{c}`")
    else:
        lines.append("- **Configuration Keys:** None")
    lines.append("")
    
    # 8. Statistics Table
    lines.append("## Detailed Statistics")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Maximum Depth | {stats.maximum_depth} |")
    lines.append(f"| Average Depth | {stats.average_depth:.2f} |")
    lines.append(f"| Leaf Count | {stats.leaf_count} |")
    lines.append(f"| Branch Count | {stats.branch_count} |")
    lines.append(f"| Node Count | {stats.node_count} |")
    lines.append(f"| Edge Count | {stats.edge_count} |")
    lines.append(f"| Recursion Count | {stats.recursion_count} |")
    lines.append(f"| Cycle Count | {stats.cycle_count} |")
    lines.append(f"| External API Count | {stats.external_api_count} |")
    lines.append(f"| Database Count | {stats.database_count} |")
    lines.append(f"| Queue Count | {stats.queue_count} |")
    lines.append(f"| Configuration Count | {stats.configuration_count} |")
    lines.append(f"| Framework Count | {stats.framework_count} |")
    lines.append(f"| Execution Path Count | {stats.execution_path_count} |")
    lines.append("")
    
    # Distributions
    if stats.language_distribution:
        lines.append("### Language Distribution")
        lines.append("| Language | Count |")
        lines.append("| --- | --- |")
        for lang, count in sorted(stats.language_distribution.items(), key=lambda x: -x[1]):
            lines.append(f"| {lang} | {count} |")
        lines.append("")
        
    if stats.node_type_distribution:
        lines.append("### Node Type Distribution")
        lines.append("| Node Type | Count |")
        lines.append("| --- | --- |")
        for nt, count in sorted(stats.node_type_distribution.items(), key=lambda x: -x[1]):
            lines.append(f"| {nt} | {count} |")
        lines.append("")
        
    if stats.edge_type_distribution:
        lines.append("### Edge Type Distribution")
        lines.append("| Edge Type | Count |")
        lines.append("| --- | --- |")
        for et, count in sorted(stats.edge_type_distribution.items(), key=lambda x: -x[1]):
            lines.append(f"| {et} | {count} |")
        lines.append("")
        
    if stats.stop_reason_distribution:
        lines.append("### Stop Reason Distribution")
        lines.append("| Stop Reason | Count |")
        lines.append("| --- | --- |")
        for sr, count in sorted(stats.stop_reason_distribution.items(), key=lambda x: -x[1]):
            lines.append(f"| {sr} | {count} |")
        lines.append("")
        
    return "\n".join(lines)


def write_journey_markdown(ir: JourneyIR, path: Path) -> None:
    """Write journey markdown to a file."""
    content = journey_to_markdown(ir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_repository_journey_summary(journeys: list[JourneyIR], path: Path) -> None:
    """Write repository-wide journey summary markdown to a file (Improvement 10)."""
    if not journeys:
        content = "# Repository Journey Summary\n\nNo journeys detected.\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return

    total_journeys = len(journeys)
    max_depth_val = max(j.statistics.maximum_depth for j in journeys)
    avg_depth_val = sum(j.statistics.average_depth for j in journeys) / total_journeys
    total_nodes = sum(j.statistics.node_count for j in journeys)
    total_edges = sum(j.statistics.edge_count for j in journeys)
    recursive_count = sum(1 for j in journeys if j.statistics.recursion_count > 0)
    cycle_count = sum(1 for j in journeys if j.statistics.cycle_count > 0)
    
    # Largest tree
    largest_tree_journey = max(journeys, key=lambda j: j.statistics.node_count)
    largest_tree_str = f"{largest_tree_journey.metadata.entry_label} ({largest_tree_journey.statistics.node_count} nodes)"
    
    # Analyze classes and files sizes
    class_counts: dict[str, int] = defaultdict(int)
    file_counts: dict[str, int] = defaultdict(int)
    languages: dict[str, int] = defaultdict(int)
    databases = set()
    queues = set()
    externals = set()
    configs = set()
    
    for j in journeys:
        all_nodes = flatten_to_list(j.root)
        for n in all_nodes:
            if n.class_name:
                class_counts[n.class_name] += 1
            if n.file_path:
                file_counts[n.file_path] += 1
            if n.language:
                languages[n.language.lower()] += 1
            
            nt_lower = (n.node_type or "").lower()
            if nt_lower in ("table", "collection", "database"):
                databases.add(n.label)
            elif nt_lower in ("topic", "queue"):
                queues.add(n.label)
            elif nt_lower in ("external", "external_api"):
                externals.add(n.label)
            elif nt_lower in ("config", "configuration"):
                configs.add(n.label)

    # Largest class (by method references in trees)
    largest_class_str = "None"
    if class_counts:
        lc, lcc = max(class_counts.items(), key=lambda x: x[1])
        largest_class_str = f"{lc} ({lcc} methods)"
        
    # Largest file
    largest_file_str = "None"
    if file_counts:
        lf, lfc = max(file_counts.items(), key=lambda x: x[1])
        lf_name = Path(lf).name
        largest_file_str = f"{lf_name} ({lfc} journeys/nodes)"
        
    # Largest API
    api_journeys = [j for j in journeys if j.metadata.journey_type.value == "api" or "api" in j.metadata.entry_id.lower()]
    largest_api_str = "None"
    if api_journeys:
        la = max(api_journeys, key=lambda j: j.statistics.maximum_depth)
        largest_api_str = f"{la.metadata.entry_label} (depth {la.statistics.maximum_depth})"
    else:
        # Fallback to any journey
        la = max(journeys, key=lambda j: j.statistics.maximum_depth)
        largest_api_str = f"{la.metadata.entry_label} (depth {la.statistics.maximum_depth})"

    # Longest path
    longest_path_len = 0
    longest_path_str = "None"
    for j in journeys:
        if j.execution_paths:
            for p in j.execution_paths:
                if len(p.nodes) > longest_path_len:
                    longest_path_len = len(p.nodes)
                    longest_path_str = f"{longest_path_len} hops ({p.labels[0]} → ... → {p.labels[-1]})"
    if longest_path_str == "None" and max_depth_val > 0:
        longest_path_str = f"{max_depth_val} hops"

    # Languages distribution percentage
    total_lang_nodes = sum(languages.values())
    lang_strs = []
    if total_lang_nodes > 0:
        for lang, cnt in sorted(languages.items(), key=lambda x: -x[1]):
            pct = (cnt / total_lang_nodes) * 100
            lang_strs.append(f"{lang} ({pct:.1f}%)")
            
    lang_distribution_str = ", ".join(lang_strs) if lang_strs else "Unknown"

    lines = [
        "# Repository Journey Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Journey Count | {total_journeys} |",
        f"| Maximum Depth | {max_depth_val} |",
        f"| Largest Tree | {largest_tree_str} |",
        f"| Largest Class | {largest_class_str} |",
        f"| Largest File | {largest_file_str} |",
        f"| Largest API | {largest_api_str} |",
        f"| Longest Path | {longest_path_str} |",
        f"| Average Depth | {avg_depth_val:.1f} |",
        f"| Total Nodes | {total_nodes} |",
        f"| Total Edges | {total_edges} |",
        f"| Recursive Methods | {recursive_count} |",
        f"| Cycles | {cycle_count} |",
        f"| External Systems | {len(externals)} |",
        f"| Databases | {len(databases)} |",
        f"| Queues | {len(queues)} |",
        f"| Configuration Keys | {len(configs)} |",
        f"| Languages | {lang_distribution_str} |",
        "",
    ]
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
