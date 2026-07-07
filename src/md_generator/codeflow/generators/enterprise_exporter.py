from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

import networkx as nx

from md_generator.codeflow.enterprise_ir.base import GRAPH_SCHEMA_VERSION
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.graph.sqlite_export import export_graph_sqlite


class EnterpriseExporter:
    def __init__(self, query: GraphQuery, output_dir: Path) -> None:
        self.query = query
        self.output_dir = output_dir

    def export_all(self, stats_payload: dict[str, Any]) -> None:
        self._before_export()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        g = self.query.g

        # 1. Export GraphML
        try:
            nx.write_graphml(g, str(self.output_dir / "graph.graphml"))
        except Exception:
            pass

        # 2. Export GEXF
        try:
            nx.write_gexf(g, str(self.output_dir / "graph.gexf"))
        except Exception:
            pass

        # 3. Export DOT file (graphviz)
        self._export_dot()

        # 4. Export CSV (Nodes and Edges)
        self._export_csv()

        # 5. Export SQLite graph.db
        self._export_sqlite()

        # 6. Export JSON (graph-full.json, repository-summary.json)
        self._export_json(stats_payload)

        # 7. Export Markdown reports
        self._export_markdown(stats_payload)
        self._after_export()

    def _before_export(self) -> None:
        """Lifecycle hook called before exporting graph artifacts."""
        pass

    def _after_export(self) -> None:
        """Lifecycle hook called after exporting graph artifacts."""
        pass

    def _export_dot(self) -> None:

        lines = ["digraph G {"]
        for u, v, data in self.query.g.edges(data=True):
            rel = data.get("edge_type", "CALLS")
            lines.append(f'  "{u}" -> "{v}" [label="{rel}"];')
        lines.append("}")
        (self.output_dir / "graph.dot").write_text("\n".join(lines), encoding="utf-8")

    def _export_csv(self) -> None:
        # Write nodes
        with open(self.output_dir / "nodes.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "kind", "language", "repository", "file", "line"])
            for n, data in self.query.g.nodes(data=True):
                w.writerow([
                    n,
                    data.get("kind", ""),
                    data.get("language", ""),
                    data.get("repository", ""),
                    data.get("file", ""),
                    data.get("line", ""),
                ])

        # Write edges
        with open(self.output_dir / "edges.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["source", "target", "edge_type", "confidence", "parser"])
            for u, v, data in self.query.g.edges(data=True):
                w.writerow([
                    u,
                    v,
                    data.get("edge_type", ""),
                    data.get("confidence", ""),
                    data.get("parser", ""),
                ])

    def _export_sqlite(self) -> None:
        db_path = self.output_dir / "graph.db"
        export_graph_sqlite(db_path, self.query.g)
        # Append graph schema versioning table
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_metadata (key TEXT PRIMARY KEY, val TEXT)")
            conn.execute(
                "INSERT OR REPLACE INTO schema_metadata (key, val) VALUES (?, ?)",
                ("schema_version", GRAPH_SCHEMA_VERSION),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def _export_json(self, stats_payload: dict[str, Any]) -> None:
        g = self.query.g
        
        # Serialize graph
        nodes = []
        for n, attr in g.nodes(data=True):
            nodes.append({"id": n, **attr})
        edges = []
        for u, v, attr in g.edges(data=True):
            edges.append({"source": u, "target": v, **attr})
            
        graph_full = {
            "graph_schema": {"version": GRAPH_SCHEMA_VERSION},
            "scan_id": g.graph.get("scan_id", ""),
            "repository": g.graph.get("repository", ""),
            "branch": g.graph.get("branch", ""),
            "commit": g.graph.get("commit", ""),
            "nodes": nodes,
            "edges": edges,
        }
        (self.output_dir / "graph-full.json").write_text(json.dumps(graph_full, indent=2), encoding="utf-8")

        summary = {
            "graph_schema": {"version": GRAPH_SCHEMA_VERSION},
            "nodes_count": g.number_of_nodes(),
            "edges_count": g.number_of_edges(),
            "stats": stats_payload,
        }
        (self.output_dir / "graph-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def _export_markdown(self, stats_payload: dict[str, Any]) -> None:
        # Create standard analysis-statistics.md
        stats_lines = [
            "# Analysis Statistics",
            "",
            "| Statistic | Value |",
            "| --- | --- |",
            f"| Files Scanned | {stats_payload.get('files_scanned', 0)} |",
            f"| Files Skipped | {stats_payload.get('files_skipped', 0)} |",
            f"| Files Failed | {stats_payload.get('files_failed', 0)} |",
            f"| Nodes Created | {stats_payload.get('nodes_created', 0)} |",
            f"| Nodes Reused | {stats_payload.get('nodes_reused', 0)} |",
            f"| Edges Created | {stats_payload.get('edges_created', 0)} |",
            f"| Cache Hits | {stats_payload.get('cache_hits', 0)} |",
            f"| Cache Misses | {stats_payload.get('cache_misses', 0)} |",
            f"| Execution Time | {stats_payload.get('execution_time_seconds', 0.0):.2f}s |",
        ]
        (self.output_dir / "analysis-statistics.md").write_text("\n".join(stats_lines), encoding="utf-8")

        # Create diagnostic.md if diagnostics present
        diag_lines = [
            "# Scan Diagnostics",
            "",
            "| Severity | File | Line | Message | Plugin |",
            "| --- | --- | --- | --- | --- |",
        ]
        for diag in stats_payload.get("diagnostics", []):
            diag_lines.append(
                f"| {diag.severity} | {diag.file} | {diag.line} | {diag.message} | {diag.plugin} |"
            )
        (self.output_dir / "diagnostics.md").write_text("\n".join(diag_lines), encoding="utf-8")
