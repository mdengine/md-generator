"""BaseVectorStore protocol and store registry."""

from typing import Protocol, List, Set, Dict, Type, Any, Optional
from md_generator.vector.exceptions import VectorStoreError
from md_generator.vector.model import CollectionConfig, EmbeddingRecord, VectorQueryResult


class BaseVectorStore(Protocol):
    """Collection-scoped vector store protocol."""

    def initialize_collection(self, config: CollectionConfig) -> None:
        ...

    def upsert_records(self, records: List[EmbeddingRecord], tenant_id: str) -> int:
        ...

    def delete_records(self, chunk_ids: List[str], tenant_id: str) -> int:
        ...

    def delete_records_by_document_id(self, document_id: str, tenant_id: str) -> int:
        ...

    def contains_embedding_ids(self, embedding_ids: List[str], tenant_id: str) -> Set[str]:
        ...

    def query(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorQueryResult]:
        ...


class StoreRegistry:
    """Registry for pluggable vector store adapters."""

    _stores: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, name: str, store_cls: Type[Any]) -> None:
        cls._stores[name.lower()] = store_cls

    @classmethod
    def get(cls, name: str) -> Type[Any]:
        key = name.lower()
        if key not in cls._stores:
            raise VectorStoreError(f"Vector store adapter '{name}' is not registered.")
        return cls._stores[key]

    @classmethod
    def list_stores(cls) -> List[str]:
        return sorted(list(cls._stores.keys()))
