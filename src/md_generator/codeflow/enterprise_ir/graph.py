from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from md_generator.codeflow.enterprise_ir.base import BaseEntity

if TYPE_CHECKING:
    from md_generator.codeflow.enterprise_ir.config import ConfigEntity
    from md_generator.codeflow.enterprise_ir.dependency import DependencyEntity
    from md_generator.codeflow.enterprise_ir.database import TableEntity, ColumnEntity, ViewEntity
    from md_generator.codeflow.enterprise_ir.query import QueryEntity
    from md_generator.codeflow.enterprise_ir.runtime import RuntimeEntity
    from md_generator.codeflow.enterprise_ir.api import ApiEntity
    from md_generator.codeflow.enterprise_ir.event import EventEntity
    from md_generator.codeflow.enterprise_ir.resource import ResourceEntity
    from md_generator.codeflow.enterprise_ir.storage import StorageEntity
    from md_generator.codeflow.enterprise_ir.queue import QueueEntity


@dataclass
class SemanticEntity(BaseEntity):
    embedding_vector: list[float] = field(default_factory=list)
    cluster_id: int | None = None
    similarity_neighbors: list[str] = field(default_factory=list)  # Neighbor entity IDs


@dataclass
class EnterpriseIR:
    configs: list[ConfigEntity] = field(default_factory=list)
    dependencies: list[DependencyEntity] = field(default_factory=list)
    queries: list[QueryEntity] = field(default_factory=list)
    resources: list[ResourceEntity] = field(default_factory=list)
    tables: list[TableEntity] = field(default_factory=list)
    columns: list[ColumnEntity] = field(default_factory=list)
    views: list[ViewEntity] = field(default_factory=list)
    queues: list[QueueEntity] = field(default_factory=list)
    storages: list[StorageEntity] = field(default_factory=list)
    events: list[EventEntity] = field(default_factory=list)
    apis: list[ApiEntity] = field(default_factory=list)
    runtime: list[RuntimeEntity] = field(default_factory=list)
    semantics: list[SemanticEntity] = field(default_factory=list)
