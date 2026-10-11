"""LangChain BaseRetriever adapter bridging to BaseVectorStore and BaseEmbeddingProvider."""

from typing import List, Optional, Dict, Any
from dataclasses import asdict
from md_generator.vector.stores.base import BaseVectorStore
from md_generator.vector.providers.base import BaseEmbeddingProvider
from md_generator.vector.model import validate_vector, VectorQueryResult
from md_generator.vector.exceptions import TenantBoundaryError, VectorError
from md_generator.adapters.langchain.exceptions import LangChainDependencyError, LangChainAdapterError

try:
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from langchain_core.documents import Document
    try:
        from pydantic import ConfigDict
        _PYDANTIC_V2 = True
    except ImportError:
        _PYDANTIC_V2 = False
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseRetriever = object  # type: ignore[misc, assignment]
    CallbackManagerForRetrieverRun = Any  # type: ignore[misc, assignment]
    Document = Any  # type: ignore[misc, assignment]
    _PYDANTIC_V2 = False
    _LANGCHAIN_AVAILABLE = False


class MDVectorStoreRetriever(BaseRetriever if _LANGCHAIN_AVAILABLE else object):  # type: ignore[misc]
    """LangChain BaseRetriever bridging to BaseVectorStore with genuine tenant immutability."""

    store: Any
    provider: Any
    tenant_id: str
    top_k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None

    if _PYDANTIC_V2:
        model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    else:
        class Config:
            frozen = True
            arbitrary_types_allowed = True

    def __init__(
        self,
        store: BaseVectorStore,
        provider: BaseEmbeddingProvider,
        tenant_id: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        if not _LANGCHAIN_AVAILABLE:
            raise LangChainDependencyError(
                "langchain-core is required to use MDVectorStoreRetriever. "
                "Install it with 'pip install langchain-core'."
            )

        if not tenant_id or not isinstance(tenant_id, str) or not tenant_id.strip():
            raise TenantBoundaryError("MDVectorStoreRetriever requires a valid non-empty tenant_id.")

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k must be a positive integer >= 1. Got: {top_k}")

        super().__init__(
            store=store,
            provider=provider,
            tenant_id=tenant_id.strip(),
            top_k=top_k,
            filter_metadata=filter_metadata,
            **kwargs,
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Enforces genuine immutability; blocks tenant modification after instantiation."""
        if name == "tenant_id" and "tenant_id" in self.__dict__:
            raise TenantBoundaryError("tenant_id is strictly immutable for MDVectorStoreRetriever.")
        super().__setattr__(name, value)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
        **kwargs: Any,
    ) -> List[Any]:
        """Executes vector retrieval lifecycle and returns LangChain Documents preserving score ranking.
        
        Explicitly rejects any runtime tenant_id override attempts in kwargs.
        """
        if "tenant_id" in kwargs:
            raise TenantBoundaryError(
                f"Runtime tenant_id override is prohibited. MDVectorStoreRetriever is strictly bound to tenant: '{self.tenant_id}'."
            )

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        try:
            # 1. Generate query embedding via provider
            vectors = self.provider.embed_texts([query])
            if not vectors or len(vectors) != 1:
                raise LangChainAdapterError(
                    f"Provider failed to produce exactly 1 vector for query. Got {len(vectors) if vectors else 0}"
                )
            query_vector = vectors[0]

            # 2. Validate query vector
            validate_vector(query_vector, expected_dimension=self.provider.dimension)

            # 3. Query vector store using bound immutable tenant_id
            results: List[VectorQueryResult] = self.store.query(
                query_vector=query_vector,
                top_k=self.top_k,
                tenant_id=self.tenant_id,
                filter_metadata=self.filter_metadata,
            )

            # 4. Map VectorQueryResult to LangChain Document preserving ranking and closing document_id provenance
            documents: List[Document] = []
            for res in results:
                doc_id = (
                    getattr(res, "document_id", None)
                    or (res.payload.get("document_id") if isinstance(res.payload, dict) else None)
                    or ""
                )

                metadata: Dict[str, Any] = {
                    "document_id": doc_id,
                    "chunk_id": res.chunk_id,
                    "embedding_id": res.embedding_id,
                    "score": res.score,
                    "semantic_key": res.semantic_key,
                    "tenant_id": res.tenant_id,
                    "entity_type": res.entity_type,
                    "parent_chunk_id": res.parent_chunk_id,
                    "source_location": asdict(res.source_location) if res.source_location else None,
                }
                if res.payload and isinstance(res.payload, dict):
                    for k, v in res.payload.items():
                        if k not in metadata:
                            metadata[k] = v

                documents.append(Document(
                    page_content=res.sanitized_content,
                    metadata=metadata,
                ))

            return documents

        except (VectorError, TenantBoundaryError, LangChainAdapterError):
            raise
        except Exception as e:
            raise LangChainAdapterError(f"Retriever query failed: {e}") from e
