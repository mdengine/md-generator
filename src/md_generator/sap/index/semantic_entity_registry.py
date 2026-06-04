from __future__ import annotations

from md_generator.sap.canonical.identity import ArtifactIdentity


class SemanticEntityRegistry:
    """Stub registry for cross-system semantic entity linking (Phase 5)."""

    def __init__(self) -> None:
        self._by_semantic: dict[str, list[ArtifactIdentity]] = {}
        self._by_stable: dict[str, ArtifactIdentity] = {}

    def register(self, identity: ArtifactIdentity) -> None:
        self._by_stable[identity.stable_id] = identity
        if identity.semantic_id:
            self._by_semantic.setdefault(identity.semantic_id, []).append(identity)

    def query_by_semantic_id(self, semantic_id: str) -> list[ArtifactIdentity]:
        return list(self._by_semantic.get(semantic_id, []))

    def get(self, stable_id: str) -> ArtifactIdentity | None:
        return self._by_stable.get(stable_id)

    def link_same_as_candidates(self, semantic_id: str) -> list[str]:
        return [i.stable_id for i in self.query_by_semantic_id(semantic_id)]
