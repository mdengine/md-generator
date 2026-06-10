from __future__ import annotations

import json
from pathlib import Path

from md_generator.odata.chunking.strategies import OdataChunk, get_strategies
from md_generator.odata.models.domain import ODataMetadataDocument


def write_odata_chunks(
    root: Path,
    documents: list[ODataMetadataDocument],
    chunk_types: list[str],
) -> list[Path]:
    chunks_dir = root / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    all_chunks: list[OdataChunk] = []
    for strat in get_strategies(chunk_types):
        all_chunks.extend(list(strat.iter_chunks(documents)))  # type: ignore[attr-defined]

    for chunk in all_chunks:
        p = chunks_dir / f"{chunk.chunk_id.replace(':', '_')}.json"
        p.write_text(
            json.dumps(
                {
                    "chunk_id": chunk.chunk_id,
                    "chunk_type": chunk.chunk_type,
                    "title": chunk.title,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        written.append(p)

    index = {
        "count": len(all_chunks),
        "chunks": [{"chunk_id": c.chunk_id, "chunk_type": c.chunk_type, "title": c.title} for c in all_chunks],
    }
    idx_path = chunks_dir / "index.json"
    idx_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    written.append(idx_path)
    return written
