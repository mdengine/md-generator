from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md_generator.codeflow.graph.query import GraphQuery


class RepositoryAnalyzer:
    def __init__(self, query: GraphQuery) -> None:
        self.query = query

    def analyze(self) -> dict[str, Any]:
        """Runs the query layer to gather configuration, dependency, database, and resource metrics."""
        configs = self.query.find_config()
        deps = self.query.find_dependencies()
        tables = self.query.find_tables()
        resources = self.query.find_resources()
        methods = self.query.find_methods()

        # Classify configs by usage
        unused_configs = [c["key"] for c in configs if c.get("usage_status") == "Unused"]
        referenced_configs = [c["key"] for c in configs if c.get("usage_status") == "Referenced"]
        missing_configs = [c["key"] for c in configs if c.get("usage_status") == "Missing"]

        # Group dependencies by type
        dep_by_type: dict[str, list[str]] = {}
        for d in deps:
            dtype = d.get("dependency_type", "External Library")
            dep_by_type.setdefault(dtype, []).append(f"{d.get('name')} ({d.get('version')})")

        # Compile resource maps
        res_by_type: dict[str, list[str]] = {}
        for r in resources:
            rtype = r.get("resource_type", "REST")
            res_by_type.setdefault(rtype, []).append(r.get("id"))

        stats = {
            "total_files": len({c.get("file") for c in configs if c.get("file")} | {d.get("file") for d in deps if d.get("file")}),
            "configs_count": len(configs),
            "unused_configs_count": len(unused_configs),
            "referenced_configs_count": len(referenced_configs),
            "missing_configs_count": len(missing_configs),
            "dependencies_count": len(deps),
            "dependency_categories": dep_by_type,
            "tables_count": len(tables),
            "tables": [t.get("table_name") for t in tables],
            "resources_count": len(resources),
            "resources": res_by_type,
            "methods_count": len(methods),
        }
        return stats

    def write_reports(self, output_dir: Path) -> None:
        stats = self.analyze()
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write repository-summary.json
        json_file = output_dir / "repository-summary.json"
        json_file.write_text(json.dumps(stats, indent=2), encoding="utf-8")

        # 2. Write repository-intelligence.md
        md_lines = [
            "# Repository Intelligence Summary",
            "",
            f"- **Scanned Files:** {stats['total_files']}",
            f"- **Declared Configuration Keys:** {stats['configs_count']}",
            f"- **Unused Configuration Keys:** {stats['unused_configs_count']}",
            f"- **Dependencies Scanned:** {stats['dependencies_count']}",
            f"- **Database Tables Discovered:** {stats['tables_count']}",
            f"- **External Clients Detected:** {stats['resources_count']}",
            "",
            "## Dependency Categories",
        ]
        for cat, items in stats["dependency_categories"].items():
            md_lines.append(f"### {cat}")
            for item in items:
                md_lines.append(f"- {item}")
        
        md_lines.extend([
            "",
            "## Configuration Analysis",
            f"Referenced: {len(stats['referenced_configs_count']) if isinstance(stats['referenced_configs_count'], list) else stats['referenced_configs_count']}",
            f"Unused: {stats['unused_configs_count']}",
            f"Missing: {stats['missing_configs_count']}",
            "",
            "## Database Schema & Tables",
        ])
        for tbl in stats["tables"]:
            md_lines.append(f"- Table: `{tbl}`")

        md_lines.extend([
            "",
            "## External Resource Maps",
        ])
        for rtype, uris in stats["resources"].items():
            md_lines.append(f"### {rtype}")
            for u in uris:
                md_lines.append(f"- `{u}`")

        md_file = output_dir / "repository-intelligence.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")
