"""Standard library in-memory collection-scoped vector store reference implementation."""

import math
from typing import List, Set, Dict, Any, Optional
from md_generator.vector.exceptions import (
    VectorStoreError,
    CollectionConfigurationError,
    TenantBoundaryError,
)
from md_generator.vector.model import (
    CollectionConfig,
    EmbeddingRecord,
    VectorQueryResult,
    validate_vector,
)
from md_generator.vector.stores.base import BaseVectorStore, StoreRegistry


class InMemoryVectorStore(BaseVectorStore):
    """Collection-scoped standard library in-memory vector store with multi-metric support."""

    def __init__(self) -> None:
        self._config: Optional[CollectionConfig] = None
        # Storage schema: records[chunk_id] = EmbeddingRecord
        self._records: Dict[str, EmbeddingRecord] = {}

    @property
    def config(self) -> Optional[CollectionConfig]:
        return self._config

    def initialize_collection(self, config: CollectionConfig) -> None:
        if not isinstance(config, CollectionConfig):
            raise CollectionConfigurationError("Invalid collection configuration provided.")

        if self._config is None:
            self._config = CollectionConfig(
                collection_name=config.collection_name,
                dimension=config.dimension,
                distance_metric=config.distance_metric,
            )
        else:
            if (
                self._config.collection_name != config.collection_name
                or self._config.dimension != config.dimension
                or self._config.distance_metric != config.distance_metric
            ):
                raise CollectionConfigurationError(
                    "Cannot re-initialize vector store with conflicting collection parameters."
                )

    def _ensure_initialized(self) -> CollectionConfig:
        if self._config is None:
            raise CollectionConfigurationError("Vector store collection is not initialized.")
        return self._config

    def _validate_tenant(self, tenant_id: str) -> None:
        if tenant_id is None or not isinstance(tenant_id, str) or tenant_id.strip() == "":
            raise TenantBoundaryError("A valid non-empty tenant_id is mandatory for vector store operations.")

    def upsert_records(self, records: List[EmbeddingRecord], tenant_id: str) -> int:
        config = self._ensure_initialized()
        self._validate_tenant(tenant_id)
        if not isinstance(records, list):
            raise VectorStoreError("records must be a list of EmbeddingRecord objects.")

        inserted_count = 0
        for rec in records:
            if not isinstance(rec, EmbeddingRecord):
                raise VectorStoreError(f"Record entry is not an EmbeddingRecord: {type(rec)}")
            if rec.tenant_id != tenant_id:
                raise TenantBoundaryError(
                    f"Record tenant_id '{rec.tenant_id}' does not match operation tenant_id '{tenant_id}'."
                )
            validate_vector(rec.vector, config.dimension)
            self._records[rec.chunk_id] = rec
            inserted_count += 1

        return inserted_count

    def delete_records(self, chunk_ids: List[str], tenant_id: str) -> int:
        self._ensure_initialized()
        self._validate_tenant(tenant_id)
        if not isinstance(chunk_ids, list):
            raise VectorStoreError("chunk_ids must be a list of strings.")

        deleted_count = 0
        for cid in chunk_ids:
            if cid in self._records:
                rec = self._records[cid]
                if rec.tenant_id == tenant_id:
                    del self._records[cid]
                    deleted_count += 1
                else:
                    raise TenantBoundaryError(
                        f"Cannot delete record '{cid}' belonging to tenant '{rec.tenant_id}' with operation tenant '{tenant_id}'."
                    )
        return deleted_count

    def delete_records_by_document_id(self, document_id: str, tenant_id: str) -> int:
        self._ensure_initialized()
        self._validate_tenant(tenant_id)
        if not document_id or not isinstance(document_id, str):
            raise VectorStoreError("document_id must be a non-empty string.")

        to_delete = [
            cid for cid, rec in self._records.items()
            if rec.document_id == document_id and rec.tenant_id == tenant_id
        ]
        for cid in to_delete:
            del self._records[cid]
        return len(to_delete)

    def contains_embedding_ids(self, embedding_ids: List[str], tenant_id: str) -> Set[str]:
        self._ensure_initialized()
        self._validate_tenant(tenant_id)
        if not isinstance(embedding_ids, list):
            raise VectorStoreError("embedding_ids must be a list of strings.")

        existing: Set[str] = set()
        target_ids = set(embedding_ids)
        for rec in self._records.values():
            if rec.tenant_id == tenant_id and rec.embedding_id in target_ids:
                existing.add(rec.embedding_id)
        return existing

    def query(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorQueryResult]:
        config = self._ensure_initialized()
        self._validate_tenant(tenant_id)

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be an integer >= 1.")

        validate_vector(query_vector, config.dimension)

        candidate_results: List[VectorQueryResult] = []

        for rec in self._records.values():
            if rec.tenant_id != tenant_id:
                continue

            # Optional filter matching
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if rec.payload.get(k) != v and getattr(rec, k, None) != v:
                        match = False
                        break
                if not match:
                    continue

            score = self._compute_score(query_vector, rec.vector, config.distance_metric)
            candidate_results.append(
                VectorQueryResult(
                    embedding_id=rec.embedding_id,
                    chunk_id=rec.chunk_id,
                    score=score,
                    sanitized_content=rec.sanitized_content,
                    semantic_key=rec.semantic_key,
                    tenant_id=rec.tenant_id,
                    entity_type=rec.entity_type,
                    parent_chunk_id=rec.parent_chunk_id,
                    source_location=rec.source_location,
                    payload=rec.payload,
                )
            )

        # Higher score = higher similarity
        candidate_results.sort(key=lambda r: r.score, reverse=True)
        return candidate_results[:top_k]

    def _compute_score(self, v1: List[float], v2: List[float], metric: str) -> float:
        if metric == "dot":
            return sum(a * b for a, b in zip(v1, v2))
        elif metric == "euclidean":
            dist = math.hypot(*[a - b for a, b in zip(v1, v2)])
            return 1.0 / (1.0 + dist)
        else:  # cosine default
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.hypot(*v1)
            norm2 = math.hypot(*v2)
            if norm1 == 0.0 or norm2 == 0.0:
                return 0.0
            return dot / (norm1 * norm2)


StoreRegistry.register("in_memory", InMemoryVectorStore)
