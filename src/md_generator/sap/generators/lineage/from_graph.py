from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import RelationshipType


def generate_lineage_json(
    artifact: CanonicalArtifact,
    store: ArtifactGraphStore,
    output_path: Path,
) -> Path:
    sid = artifact.identity.stable_id
    upstream = store.upstream(
        sid,
        relationship_types={
            RelationshipType.READS_FROM,
            RelationshipType.DERIVES_FROM,
            RelationshipType.JOINS,
        },
    )
    downstream = store.downstream(
        sid,
        relationship_types={
            RelationshipType.TRANSFORMS,
            RelationshipType.EXPOSES,
            RelationshipType.SERVES,
        },
    )
    payload = {
        "artifact_id": sid,
        "upstream": sorted(upstream),
        "downstream": sorted(downstream),
        "column_lineage": [
            e.model_dump(mode="json")
            for e in store.column_lineage(sid)
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def generate_impact_markdown(
    artifact: CanonicalArtifact,
    store: ArtifactGraphStore,
    output_path: Path,
) -> Path:
    sid = artifact.identity.stable_id
    impacted = store.downstream(sid)
    lines = [
        f"# Impact analysis: {artifact.name}",
        "",
        f"**Stable ID:** `{sid}`",
        "",
        "## Downstream dependents",
        "",
    ]
    if impacted:
        for node_id in sorted(impacted):
            node = store.graph.nodes.get(node_id)
            label = node.label if node else node_id
            lines.append(f"- {label} (`{node_id}`)")
    else:
        lines.append("_No downstream dependents found._")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
