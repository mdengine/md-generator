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
        elif rule_id == "bw-adso-missing-key" and artifact.artifact_type == "bw.adso":
            fields = getattr(artifact, "fields", [])
            has_key = any("key" in str(f).lower() or "id" in str(f).lower() for f in fields)
            if not fields or not has_key:
                return {
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "warning"),
                    "message": f"ADSO {artifact.name} has no key fields defined",
                    "artifact_id": artifact.identity.stable_id,
                }
        elif rule_id == "bw-dtp-no-filter" and artifact.artifact_type == "bw.dtp":
            meta = artifact.metadata.get("bw", {}) or artifact.metadata
            filter_val = meta.get("filter") or meta.get("delta_filter")
            if not filter_val:
                return {
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "info"),
                    "message": f"DTP {artifact.name} has no delta filter — may cause full load every run",
                    "artifact_id": artifact.identity.stable_id,
                }
        elif rule_id == "bw-composite-provider-many-parts" and artifact.artifact_type == "bw.composite_provider":
            members = getattr(artifact, "members", [])
            if len(members) > 3:
                return {
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "info"),
                    "message": f"Composite provider {artifact.name} has {len(members)} parts — check for performance impact",
                    "artifact_id": artifact.identity.stable_id,
                }
        elif rule_id == "datasphere-dataflow-no-target" and artifact.artifact_type == "datasphere.data_flow":
            steps = getattr(artifact, "steps", [])
            has_target = any(step.get("kind") in ("target", "sink") for step in steps if isinstance(step, dict))
            if not has_target:
                return {
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "warning"),
                    "message": f"Data flow {artifact.name} has no defined target entity",
                    "artifact_id": artifact.identity.stable_id,
                }
        elif rule_id == "abap-dynamic-sql-risk" and artifact.artifact_type == "abap.program":
            abap_meta = artifact.metadata.get("abap", {})
            signals = abap_meta.get("dynamic_sql_signals", [])
            if signals:
                return {
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "warning"),
                    "message": f"Program {artifact.name} contains dynamic SQL — lineage may be incomplete",
                    "artifact_id": artifact.identity.stable_id,
                }
        elif rule_id == "abap-high-complexity-query" and artifact.artifact_type == "abap.program":
            abap_meta = artifact.metadata.get("abap", {})
            sql_stmts = abap_meta.get("sql_statements", [])
            high_complexity = any(stmt.get("complexity", {}).get("complexity_score", 0) > 5.0 for stmt in sql_stmts if isinstance(stmt, dict))
            if high_complexity:
                return {
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "info"),
                    "message": f"Program {artifact.name} has high SQL complexity score",
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
