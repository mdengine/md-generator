from __future__ import annotations

import hashlib
import json
from pathlib import Path
from md_generator.sap.abap_journey.models import CallGraph, Node, Edge, RelationshipType

class IncrementalCache:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_hash(self, path: Path) -> str:
        if not path.exists():
            return ""
        try:
            content = path.read_bytes()
            # Combine content hash with structural schema versions to prevent stale cache hits
            version_suffix = b"parser:1.0;schema:1.0;framework:1.0"
            hasher = hashlib.sha256()
            hasher.update(content)
            hasher.update(version_suffix)
            return hasher.hexdigest()
        except Exception:
            return ""

    def get(self, source_path: Path) -> CallGraph | None:
        file_hash = self.get_hash(source_path)
        if not file_hash:
            return None

        cache_file = self.cache_dir / f"{file_hash}.json"
        if cache_file.exists():
            try:
                from md_generator.sap.abap_journey.models import GraphSerializer
                return GraphSerializer.from_json(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def put(self, source_path: Path, graph: CallGraph) -> None:
        file_hash = self.get_hash(source_path)
        if not file_hash:
            return

        cache_file = self.cache_dir / f"{file_hash}.json"
        try:
            from md_generator.sap.abap_journey.models import GraphSerializer
            cache_file.write_text(GraphSerializer.to_json(graph), encoding="utf-8")
        except Exception:
            pass
