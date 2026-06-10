from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from md_generator.sap.canonical.base import CanonicalArtifact


class DeterministicRuleEngine:
    def __init__(self, catalog_path: Path | None = None) -> None:
        self._rules: list[dict[str, Any]] = []
        if catalog_path and catalog_path.is_file():
            data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
            self._rules = list(data.get("rules", []))

    def evaluate(self, artifact: CanonicalArtifact, graph_store: object) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for rule in self._rules:
            if rule.get("artifact_type") and rule["artifact_type"] != artifact.artifact_type:
                continue
            finding = self._apply_rule(rule, artifact, graph_store)
            if finding:
                findings.append(finding)
        findings.extend(self._builtin_rules(artifact, graph_store))
        return findings

    def _apply_rule(self, rule: dict[str, Any], artifact: CanonicalArtifact, graph_store: object) -> dict | None:
        rule_id = rule.get("id", "")
        if rule_id == "unused-columns-hana" and artifact.artifact_type == "hana.calculation_view":
            tg = artifact.metadata.get("transformation_graph", {})
            nodes = tg.get("nodes", {})
            for nid, node in nodes.items():
                if node.get("node_kind") == "projection":
                    props = node.get("properties", {})
                    unused = props.get("unused_columns", [])
                    if unused:
                        return {
                            "rule_id": rule_id,
                            "severity": rule.get("severity", "info"),
                            "message": f"Unused columns in projection {nid}: {', '.join(unused)}",
                            "artifact_id": artifact.identity.stable_id,
                        }
        return None

    def _builtin_rules(self, artifact: CanonicalArtifact, graph_store: object) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        if artifact.artifact_type == "hana.calculation_view":
            tg_meta = artifact.metadata.get("transformation_graph", {})
            join_count = sum(
                1 for n in tg_meta.get("nodes", {}).values() if n.get("node_kind") == "join"
            )
            if join_count > 5:
                findings.append(
                    {
                        "rule_id": "hana-expensive-joins",
                        "severity": "warning",
                        "message": f"Calculation view has {join_count} join nodes",
                        "artifact_id": artifact.identity.stable_id,
                        "semantic_tags": ["performance"],
                    }
                )
        return findings
