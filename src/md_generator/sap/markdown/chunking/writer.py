from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md_generator.core.artifacts.models import ArtifactMetadata, MarkdownArtifact
from md_generator.governance.lineage import apply_lineage
from md_generator.log.chunking.artifact_adapter import semantic_chunk_to_artifact
from md_generator.log.chunking.chunk_models import SemanticChunk
from md_generator.sap.markdown.chunking.registry import get_strategies
from md_generator.sap.models.entities.sap_object import SapObject


def write_semantic_chunks(
    root: Path,
    objects: list[SapObject],
    chunk_types: list[str],
    *,
    config_hash: str = "",
    **kwargs: Any,
) -> list[Path]:
    out_dir = root / "chunks"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    artifacts: list[MarkdownArtifact] = []
    index: list[dict[str, Any]] = []

    for strategy in get_strategies(chunk_types):
        for ch in strategy.iter_chunks(objects, **kwargs):
            art = semantic_chunk_to_artifact(ch)
            if config_hash:
                apply_lineage([art], config_hash=config_hash, source_file=ch.source_refs[0] if ch.source_refs else None)
            artifacts.append(art)
            p = out_dir / f"{ch.chunk_id.replace(':', '_')}.md"
            fm = art.to_frontmatter_dict()
            body = f"---\n{json.dumps(fm, indent=2)}\n---\n\n{ch.content}\n"
            p.write_text(body, encoding="utf-8")
            written.append(p)
            index.append({"chunk_id": ch.chunk_id, "chunk_type": ch.chunk_type, "path": p.name})

    idx_path = out_dir / "index.json"
    idx_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    written.append(idx_path)

    jsonl = out_dir / "chunks.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for art in artifacts:
            f.write(json.dumps({"id": art.artifact_id, "type": art.artifact_type, "title": art.title}) + "\n")
    written.append(jsonl)
    return written
