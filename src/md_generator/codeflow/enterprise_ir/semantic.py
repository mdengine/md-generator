from __future__ import annotations

from dataclasses import dataclass, field
from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class SemanticEntity(BaseEntity):
    embedding_vector: list[float] = field(default_factory=list)
    cluster_id: int | None = None
    similarity_neighbors: list[str] = field(default_factory=list)  # Neighbor entity IDs
    tags: list[str] = field(default_factory=list)


@dataclass
class SemanticRelation(BaseEntity):
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""
    similarity_score: float = 0.0


@dataclass
class SemanticGroup(BaseEntity):
    group_name: str = ""
    entity_ids: list[str] = field(default_factory=list)
    description: str | None = None


@dataclass
class SemanticCluster(BaseEntity):
    cluster_id: int = 0
    centroid: list[float] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)


@dataclass
class SemanticTag(BaseEntity):
    tag_name: str = ""
    tagged_entities: list[str] = field(default_factory=list)
