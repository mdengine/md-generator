from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph


def render_transformation_mermaid(
    artifact: CanonicalArtifact,
    output_path: Path,
) -> Path:
    tg_data = artifact.metadata.get("transformation_graph")
    if not tg_data:
        lines = ["flowchart LR", f'  root["{artifact.name}"]']
    else:
        tg = TransformationGraph.model_validate(tg_data)
        lines = ["flowchart LR"]
        for node in tg.nodes.values():
            safe = node.node_id.replace('"', "'")
            lines.append(f'  {safe}["{node.node_kind}: {safe}"]')
        for node in tg.nodes.values():
            for out_id in node.outputs:
                if out_id in tg.nodes:
                    lines.append(f"  {node.node_id} --> {out_id}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
