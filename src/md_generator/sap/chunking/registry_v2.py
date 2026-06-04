from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.chunking.spec import SemanticChunkSpec


class SemanticChunkRegistryV2:
    def __init__(self) -> None:
        self._chunks: list[SemanticChunkSpec] = []

    def register(self, chunk: SemanticChunkSpec) -> None:
        self._chunks.append(chunk)

    @property
    def chunks(self) -> list[SemanticChunkSpec]:
        return list(self._chunks)

    def write_jsonl(self, path: Path) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for chunk in self._chunks:
                fh.write(json.dumps(chunk.to_jsonl_record(), ensure_ascii=False) + "\n")
        return len(self._chunks)
