from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol

from md_generator.log.chunking.chunk_models import SemanticChunk
from md_generator.sap.models.entities.sap_object import SapObject


class SapChunkStrategy(Protocol):
    name: str

    def iter_chunks(
        self,
        objects: list[SapObject],
        *,
        relationships: dict[str, list[dict[str, Any]]] | None = None,
        validations: list[dict[str, Any]] | None = None,
        auth_checks: list[dict[str, Any]] | None = None,
        lineage: dict[str, list[dict[str, Any]]] | None = None,
    ) -> Iterator[SemanticChunk]: ...


class EntityChunkStrategy:
    name = "entity"

    def iter_chunks(self, objects: list[SapObject], **kwargs: Any) -> Iterator[SemanticChunk]:
        for obj in objects:
            yield SemanticChunk(
                chunk_id=f"entity:{obj.object_id}",
                chunk_type=self.name,
                title=f"{obj.semantic_entity or obj.name}",
                content=f"SAP {obj.kind.value} {obj.name} in package {obj.package}",
                metadata={"object_id": obj.object_id, "kind": obj.kind.value, "tags": obj.tags},
                source_refs=[str(obj.source_path)] if obj.source_path else [],
            )


class RelationshipChunkStrategy:
    name = "relationship"

    def iter_chunks(self, objects: list[SapObject], **kwargs: Any) -> Iterator[SemanticChunk]:
        rels = kwargs.get("relationships") or {}
        for obj in objects:
            for r in rels.get(obj.object_id, [])[:20]:
                yield SemanticChunk(
                    chunk_id=f"rel:{obj.object_id}:{r.get('target_id', '')}",
                    chunk_type=self.name,
                    title=f"{obj.name} → {r.get('target_name', '?')}",
                    content=f"Relation {r.get('relation')} from {obj.name} to {r.get('target_name')}",
                    metadata={"relation": r.get("relation"), "source": obj.object_id},
                )


class ValidationChunkStrategy:
    name = "validation"

    def iter_chunks(self, objects: list[SapObject], **kwargs: Any) -> Iterator[SemanticChunk]:
        for v in kwargs.get("validations") or []:
            yield SemanticChunk(
                chunk_id=f"val:{v.get('source')}:{v.get('line', 0)}",
                chunk_type=self.name,
                title=f"Validation {v.get('rule_type')}",
                content=v.get("expression", ""),
                metadata=v,
            )


class AuthorizationChunkStrategy:
    name = "authorization"

    def iter_chunks(self, objects: list[SapObject], **kwargs: Any) -> Iterator[SemanticChunk]:
        for a in kwargs.get("auth_checks") or []:
            yield SemanticChunk(
                chunk_id=f"auth:{a.get('program')}:{a.get('object')}",
                chunk_type=self.name,
                title=f"AUTH {a.get('object')}",
                content=f"Program {a.get('program')} checks {a.get('object')}",
                metadata=a,
            )


class LineageChunkStrategy:
    name = "lineage"

    def iter_chunks(self, objects: list[SapObject], **kwargs: Any) -> Iterator[SemanticChunk]:
        lin = kwargs.get("lineage") or {}
        for obj in objects:
            entries = lin.get(obj.object_id) or []
            if not entries:
                continue
            yield SemanticChunk(
                chunk_id=f"lineage:{obj.object_id}",
                chunk_type=self.name,
                title=f"Lineage {obj.name}",
                content=str(entries[0]),
                metadata={"object_id": obj.object_id},
            )
