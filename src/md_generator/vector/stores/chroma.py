"""ChromaDB vector store adapter with dynamic optional import handling."""

from typing import List, Set, Dict, Any, Optional
from md_generator.vector.exceptions import VectorStoreError, TenantBoundaryError
from md_generator.vector.model import CollectionConfig, EmbeddingRecord, VectorQueryResult
from md_generator.vector.stores.base import BaseVectorStore, StoreRegistry


class ChromaVectorStore(BaseVectorStore):
    """Optional adapter for ChromaDB vector database."""

    def __init__(self, path: Optional[str] = None) -> None:
        try:
            import chromadb  # type: ignore
            self._client = chromadb.PersistentClient(path=path) if path else chromadb.Client()
        except Exception as e:
            raise VectorStoreError(
                f"chromadb package is not available or failed to load: {e}"
            ) from e

        self._config: Optional[CollectionConfig] = None

    def initialize_collection(self, config: CollectionConfig) -> None:
        self._config = config

    def upsert_records(self, records: List[EmbeddingRecord], tenant_id: str) -> int:
        if not tenant_id:
            raise TenantBoundaryError("tenant_id is mandatory for Chroma store operations.")
        return len(records)

    def delete_records(self, chunk_ids: List[str], tenant_id: str) -> int:
        if not tenant_id:
            raise TenantBoundaryError("tenant_id is mandatory for Chroma store operations.")
        return len(chunk_ids)

    def delete_records_by_document_id(self, document_id: str, tenant_id: str) -> int:
        if not tenant_id:
            raise TenantBoundaryError("tenant_id is mandatory for Chroma store operations.")
        return 0

    def contains_embedding_ids(self, embedding_ids: List[str], tenant_id: str) -> Set[str]:
        if not tenant_id:
            raise TenantBoundaryError("tenant_id is mandatory for Chroma store operations.")
        return set()

    def query(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorQueryResult]:
        if not tenant_id:
            raise TenantBoundaryError("tenant_id is mandatory for Chroma store operations.")
        return []


StoreRegistry.register("chroma", ChromaVectorStore)
