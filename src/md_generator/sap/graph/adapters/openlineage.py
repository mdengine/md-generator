from __future__ import annotations

from typing import Any

from md_generator.sap.graph.model import ArtifactGraph
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import RelationshipType


class OpenLineageMapper:
    """Maps internal ArtifactGraph to OpenLineage-style dict (stub export)."""

    def __init__(self, run_id: str = "", job_name: str = "md-sap") -> None:
        self.run_id = run_id
        self.job_name = job_name

    def to_openlineage(self, store: ArtifactGraphStore) -> dict[str, Any]:
        graph = store.graph
        datasets = [
            {
                "name": node.label or node.node_id,
                "namespace": node.namespace or "sap",
                "facets": {"schema": node.properties.get("schema", {})},
            }
            for node in graph.nodes.values()
            if node.node_kind in ("artifact", "dataset", "source", "sink")
        ]
        inputs: list[dict[str, str]] = []
        outputs: list[dict[str, str]] = []
        for edge in graph.edges.values():
            if edge.relationship in (
                RelationshipType.READS_FROM,
                RelationshipType.DERIVES_FROM,
            ):
                inputs.append({"namespace": "sap", "name": edge.source_id})
                outputs.append({"namespace": "sap", "name": edge.target_id})
        return {
            "eventType": "COMPLETE",
            "eventTime": "",
            "run": {"runId": self.run_id},
            "job": {"namespace": "md-sap", "name": self.job_name},
            "inputs": _dedupe_datasets(inputs),
            "outputs": _dedupe_datasets(outputs),
            "datasets": datasets,
            "columnLineage": self._column_lineage(graph),
        }

    def _column_lineage(self, graph: ArtifactGraph) -> list[dict[str, Any]]:
        facets: list[dict[str, Any]] = []
        for edge in graph.edges.values():
            if edge.relationship not in (RelationshipType.DERIVES_FROM, RelationshipType.TRANSFORMS):
                continue
            facets.append(
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "fields": edge.properties.get("column_mapping", []),
                }
            )
        return facets


def _dedupe_datasets(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for item in items:
        key = (item.get("namespace", ""), item.get("name", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
