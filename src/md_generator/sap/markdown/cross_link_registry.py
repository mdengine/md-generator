from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.graph.model import GraphEdge, GraphNode
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.markdown.relationship_weights import relationship_weight
from md_generator.sap.markdown.resolved_link import (
    CONFIDENCE_BY_STRATEGY,
    ResolvedLink,
    unresolved_link,
)
from md_generator.sap.markdown.builders.renderer_context import (
    TYPE_KIND_TO_PATH_KINDS,
    PathKey,
)

_DEFAULT_REL_TYPES = (
    RelationshipType.REFERENCES,
    RelationshipType.CONTAINS,
    RelationshipType.READS_FROM,
)


@dataclass
class CrossLinkRegistry:
    path_registry: dict[PathKey, str] = field(default_factory=dict)
    link_graph: SapLinkGraph | None = None
    graph_store: ArtifactGraphStore | None = None
    artifact_by_name: dict[str, CanonicalArtifact] = field(default_factory=dict)
    stable_id_by_name: dict[str, str] = field(default_factory=dict)
    _cache: dict[tuple[str, ...], ResolvedLink] = field(default_factory=dict)
    _chain_cache: dict[str, list[ResolvedLink]] = field(default_factory=dict)

    def resolve_link(self, kind: str, name: str) -> ResolvedLink:
        cache_key = ("link", kind.upper(), name.upper())
        if cache_key in self._cache:
            return self._cache[cache_key]
        target = name.upper()
        if not target:
            link = unresolved_link("", reason="empty name")
            self._cache[cache_key] = link
            return link
        for strategy_fn in (
            lambda: self._from_path_registry(kind, target),
            lambda: self._from_graph_label(target),
            lambda: self._from_link_graph(kind, target),
        ):
            link = strategy_fn()
            if link.strategy != "unresolved":
                self._cache[cache_key] = link
                return link
        link = ResolvedLink(
            target=target,
            href=None,
            stable_id=self.stable_id_by_name.get(target, ""),
            confidence=CONFIDENCE_BY_STRATEGY["heuristic_label"],
            strategy="heuristic_label",
            source="cross_link_registry",
            match_reason="name known; no path",
        )
        self._cache[cache_key] = link
        return link

    def resolve_type_reference(self, type_kind: str, type_name: str) -> ResolvedLink:
        cache_key = ("type", type_kind.lower(), type_name.upper())
        if cache_key in self._cache:
            return self._cache[cache_key]
        tk = type_kind.replace("_", "").lower()
        kinds = TYPE_KIND_TO_PATH_KINDS.get(
            tk, ["DATA_ELEMENT", "DOMAIN", "STRUCTURE", "CDS_STRUCTURE", "TABLE"]
        )
        for kind in kinds:
            link = self.resolve_link(kind, type_name)
            if link.href:
                self._cache[cache_key] = link
                return link
        for kind in ("DATA_ELEMENT", "DOMAIN"):
            link = self.resolve_link(kind, type_name)
            if link.href:
                self._cache[cache_key] = link
                return link
        link = self.resolve_link("", type_name)
        self._cache[cache_key] = link
        return link

    def _from_path_registry(self, kind: str, target: str) -> ResolvedLink:
        key = (kind.upper(), target)
        href = self.path_registry.get(key)
        if not href and kind:
            return unresolved_link(target, reason="path_registry miss")
        if not href:
            for k in TYPE_KIND_TO_PATH_KINDS.get("", []):
                href = self.path_registry.get((k, target))
                if href:
                    kind = k
                    break
            if not href:
                for path_key, path in self.path_registry.items():
                    if path_key[1] == target:
                        href = path
                        kind = path_key[0]
                        break
        if not href:
            return unresolved_link(target, reason="path_registry miss")
        art = self.artifact_by_name.get(target)
        return ResolvedLink(
            target=target,
            href=href,
            stable_id=art.identity.stable_id if art else self.stable_id_by_name.get(target, ""),
            confidence=CONFIDENCE_BY_STRATEGY["path_registry"],
            strategy="path_registry",
            source="cross_link_registry",
            match_reason=f"{kind}:{target}",
        )

    def _from_graph_label(self, target: str) -> ResolvedLink:
        store = self.graph_store
        if not store:
            return unresolved_link(target, reason="no graph store")
        for node in store.graph.nodes.values():
            if node.label.upper() == target or node.node_id.upper().endswith(target):
                art = self.artifact_by_name.get(target)
                href = None
                if art:
                    from md_generator.sap.markdown.builders.renderer_context import (
                        ARTIFACT_TYPE_TO_PATH_KIND,
                        _artifact_md_path,
                    )

                    slug = art.name.lower().replace(" ", "-").replace("/", "-").replace("::", "-")
                    href = self.path_registry.get(
                        (ARTIFACT_TYPE_TO_PATH_KIND.get(art.artifact_type, ""), target)
                    ) or _artifact_md_path(art.artifact_type, slug)
                return ResolvedLink(
                    target=target,
                    href=href,
                    stable_id=node.node_id,
                    confidence=CONFIDENCE_BY_STRATEGY["graph_walk"],
                    strategy="graph_walk",
                    source="cross_link_registry",
                    match_reason=f"graph node {node.label}",
                )
        return unresolved_link(target, reason="graph miss")

    def _from_link_graph(self, kind: str, target: str) -> ResolvedLink:
        lg = self.link_graph
        if not lg:
            return unresolved_link(target, reason="no link graph")
        path = lg.path_for(kind, "", target) or lg.path_for(kind.lower(), "", target)
        if not path:
            return unresolved_link(target, reason="link_graph miss")
        return ResolvedLink(
            target=target,
            href=path,
            confidence=CONFIDENCE_BY_STRATEGY["path_registry"],
            strategy="path_registry",
            source="cross_link_registry",
            match_reason="link_graph entity path",
        )

    def neighbors_for_render(
        self,
        stable_id: str,
        relationship_types: Iterable[RelationshipType] | None = None,
        *,
        max_depth: int = 3,
    ) -> list[tuple[GraphNode, GraphEdge]]:
        store = self.graph_store
        if not store or not stable_id:
            return []
        allowed = set(relationship_types or _DEFAULT_REL_TYPES)
        results: list[tuple[GraphNode, GraphEdge]] = []
        seen_edges: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(stable_id, 0)])
        visited: set[str] = {stable_id}
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in store.graph.edges.values():
                if edge.source_id != current or edge.relationship not in allowed:
                    continue
                if edge.edge_id in seen_edges:
                    continue
                seen_edges.add(edge.edge_id)
                node = store.graph.nodes.get(edge.target_id)
                if node:
                    results.append((node, edge))
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, depth + 1))
        results.sort(
            key=lambda pair: (
                -relationship_weight(pair[1].relationship),
                pair[0].label.upper(),
            )
        )
        return results

    def related_ddic_chain(self, de_name: str) -> list[ResolvedLink]:
        key = de_name.upper()
        if key in self._chain_cache:
            return self._chain_cache[key]
        chain: list[ResolvedLink] = []
        de_link = self.resolve_link("DATA_ELEMENT", de_name)
        chain.append(de_link)
        art = self.artifact_by_name.get(key)
        if art:
            meta = art.metadata.get("data_element") or {}
            type_kind = meta.get("type_kind", "")
            type_name = meta.get("type_name", "")
            if type_name:
                chain.append(self.resolve_type_reference(type_kind, type_name))
        self._chain_cache[key] = chain
        return chain


def build_cross_link_registry(
    *,
    path_registry: dict[PathKey, str],
    graph_store: ArtifactGraphStore | None = None,
    link_graph: SapLinkGraph | None = None,
    artifacts: list[CanonicalArtifact] | None = None,
) -> CrossLinkRegistry:
    by_name: dict[str, CanonicalArtifact] = {}
    stable_by_name: dict[str, str] = {}
    for art in artifacts or []:
        by_name[art.name.upper()] = art
        stable_by_name[art.name.upper()] = art.identity.stable_id
    return CrossLinkRegistry(
        path_registry=path_registry,
        link_graph=link_graph,
        graph_store=graph_store,
        artifact_by_name=by_name,
        stable_id_by_name=stable_by_name,
    )
