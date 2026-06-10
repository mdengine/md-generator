from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact


class MetadataIndex:
    def __init__(self, index_dir: Path) -> None:
        self._index_dir = index_dir
        self._entries: dict[str, dict] = {}

    def register(self, artifact: CanonicalArtifact) -> None:
        self._entries[artifact.identity.stable_id] = {
            "stable_id": artifact.identity.stable_id,
            "physical_id": artifact.identity.physical_id,
            "semantic_id": artifact.identity.semantic_id,
            "artifact_type": artifact.artifact_type,
            "name": artifact.name,
            "namespace": artifact.identity.namespace,
            "source_path": artifact.source_path,
        }

    def write(self) -> Path:
        self._index_dir.mkdir(parents=True, exist_ok=True)
        path = self._index_dir / "metadata_index.json"
        path.write_text(json.dumps({"artifacts": list(self._entries.values())}, indent=2), encoding="utf-8")
        return path

    def lookup(self, stable_id: str) -> dict | None:
        return self._entries.get(stable_id)
