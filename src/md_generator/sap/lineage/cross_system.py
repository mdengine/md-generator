from __future__ import annotations

from md_generator.sap.graph.model import GraphEdge
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.index.semantic_entity_registry import SemanticEntityRegistry


def link_cross_system_lineage(store: ArtifactGraphStore, registry: SemanticEntityRegistry) -> int:
    """Link artifacts sharing semantic_id via SAME_AS edges."""
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
                edge_id = f"same_as:{a}:{b}"
                store.add_edge(
                    GraphEdge(
                        edge_id=edge_id,
                        source_id=a,
                        target_id=b,
                        relationship=RelationshipType.SAME_AS,
                        properties={"semantic_id": semantic_id},
                    )
                )
                linked += 1
    return linked
