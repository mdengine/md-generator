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
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""

    def get(self, source_path: Path) -> CallGraph | None:
        file_hash = self.get_hash(source_path)
        if not file_hash:
            return None

        cache_file = self.cache_dir / f"{file_hash}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                graph = CallGraph()
                for nid, nd in data.get("nodes", {}).items():
                    graph.add_node(Node(**nd))
                for ed in data.get("edges", []):
                    ed["relationship"] = RelationshipType(ed["relationship"])
                    graph.add_edge(Edge(**ed))
                return graph
            except Exception:
                pass
        return None

    def put(self, source_path: Path, graph: CallGraph) -> None:
        file_hash = self.get_hash(source_path)
        if not file_hash:
            return

        cache_file = self.cache_dir / f"{file_hash}.json"
        try:
            cache_file.write_text(json.dumps(graph.to_dict(), indent=2), encoding="utf-8")
        except Exception:
            pass
