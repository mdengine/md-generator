from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.markdown.builders.renderer_context import (
    ARTIFACT_TYPE_TO_PATH_KIND,
    PathKey,
    _artifact_md_path,
    build_path_registry,
)


@dataclass
class NavigationEntry:
    name: str
    kind: str
    stable_id: str
    artifact_type: str
    entity_path: str | None = None
    canonical_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        paths: dict[str, str] = {}
        if self.entity_path:
            paths["entity"] = self.entity_path
        if self.canonical_path:
            paths["canonical"] = self.canonical_path
        return {
            "name": self.name,
            "kind": self.kind,
            "stable_id": self.stable_id,
            "artifact_type": self.artifact_type,
            "paths": paths,
        }


@dataclass
class UnifiedOutputRegistry:
    entries: dict[str, NavigationEntry] = field(default_factory=dict)
    path_registry: dict[PathKey, str] = field(default_factory=dict)

    def register_artifact(
        self,
        artifact: CanonicalArtifact,
        *,
        entity_path: str | None = None,
        canonical_path: str | None = None,
    ) -> None:
        kind = ARTIFACT_TYPE_TO_PATH_KIND.get(artifact.artifact_type, "")
        if not kind:
            return
        slug = artifact.name.lower().replace(" ", "-").replace("/", "-").replace("::", "-")
        canonical = canonical_path or _artifact_md_path(artifact.artifact_type, slug)
        entry = NavigationEntry(
            name=artifact.name.upper(),
            kind=kind,
            stable_id=artifact.identity.stable_id,
            artifact_type=artifact.artifact_type,
            entity_path=entity_path,
            canonical_path=canonical,
        )
        self.entries[artifact.identity.stable_id] = entry
        self.path_registry[(kind, artifact.name.upper())] = canonical
        if artifact.artifact_type in ("ddic.structure", "cds.structure"):
            self.path_registry[("STRUCTURE", artifact.name.upper())] = canonical

    def merge_path_registry(self, extra: dict[PathKey, str]) -> None:
        self.path_registry.update(extra)

    def write_navigation_index(
        self,
        output_dir: Path,
        *,
        run_id: str = "",
        schema_version: str = "1.0.0",
    ) -> Path:
        index_path = output_dir / "navigation" / "index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": schema_version,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "run_id": run_id,
            "entries": sorted(
                (e.to_dict() for e in self.entries.values()),
                key=lambda x: (x["kind"], x["name"]),
            ),
        }
        index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return index_path


def build_unified_output_registry(
    artifacts: list[CanonicalArtifact],
    link_graph: SapLinkGraph | None = None,
) -> UnifiedOutputRegistry:
    registry = UnifiedOutputRegistry()
    registry.merge_path_registry(build_path_registry(artifacts))
    for artifact in artifacts:
        entity_path = None
        if link_graph:
            kind = ARTIFACT_TYPE_TO_PATH_KIND.get(artifact.artifact_type, artifact.artifact_type)
            entity_path = (
                link_graph.entity_path_for(kind, artifact.name, artifact.package or "")
                or link_graph.entity_path_for(artifact.artifact_type, artifact.name, artifact.package or "")
            )
        registry.register_artifact(artifact, entity_path=entity_path)
        entry = registry.entries.get(artifact.identity.stable_id)
        if link_graph and entry and entry.canonical_path:
            kind = ARTIFACT_TYPE_TO_PATH_KIND.get(artifact.artifact_type, "")
            if kind:
                link_graph.register_canonical(kind, artifact.name, entry.canonical_path)
    return registry
