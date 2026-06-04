from __future__ import annotations

from md_generator.sap.graph.model import GraphEdge
from md_generator.sap.graph.backends.protocol import GraphStore
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.index.semantic_entity_registry import SemanticEntityRegistry
from md_generator.sap.lineage.semantic_match import SemanticMatch


def _match_by_physical_name(registry: SemanticEntityRegistry) -> list[tuple[str, str, SemanticMatch]]:
    """Link artifacts with same physical_id (case-insensitive) across namespaces."""
    by_physical: dict[str, list[str]] = {}
    for ident in registry._by_stable.values():
        key = (ident.physical_id or ident.display_id or "").upper()
        if not key:
            continue
        by_physical.setdefault(key, []).append(ident.stable_id)
    out: list[tuple[str, str, SemanticMatch]] = []
    for physical, stable_ids in by_physical.items():
        if len(stable_ids) < 2:
            continue
        for i, a in enumerate(stable_ids):
            for b in stable_ids[i + 1 :]:
                match = SemanticMatch(
                    confidence_score=0.85,
                    matching_strategy="physical_name_match",
                    match_reason=f"Shared physical name '{physical}'",
                )
                out.append((a, b, match))
    return out


def link_cross_system_lineage(store: GraphStore, registry: SemanticEntityRegistry) -> int:
    """Link artifacts via semantic_id and physical name with confidence metadata."""
    linked = 0
    seen_pairs: set[tuple[str, str]] = set()

    semantic_ids = {i.semantic_id for i in registry._by_stable.values() if i.semantic_id}
    for semantic_id in semantic_ids:
        identities = registry.query_by_semantic_id(semantic_id)
        stable_ids = [i.stable_id for i in identities]
        for i, a in enumerate(stable_ids):
            for b in stable_ids[i + 1 :]:
                pair = tuple(sorted((a, b)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                match = SemanticMatch(
                    confidence_score=1.0,
                    matching_strategy="semantic_id",
                    match_reason=f"Shared semantic_id '{semantic_id}'",
                )
                store.add_edge(
                    GraphEdge(
                        edge_id=f"same_as:{a}:{b}",
                        source_id=a,
                        target_id=b,
                        relationship=RelationshipType.SAME_AS,
                        properties={**match.to_edge_properties(), "semantic_id": semantic_id},
                    )
                )
                linked += 1

    for a, b, match in _match_by_physical_name(registry):
        pair = tuple(sorted((a, b)))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        store.add_edge(
            GraphEdge(
                edge_id=f"same_as:{a}:{b}",
                source_id=a,
                target_id=b,
                relationship=RelationshipType.SAME_AS,
                properties=match.to_edge_properties(),
            )
        )
        linked += 1
    return linked
