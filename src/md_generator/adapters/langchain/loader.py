"""LangChain DocumentLoader adapter for SemanticDocument and SemanticChunk models."""

from typing import List, Optional, Dict, Any, Iterator
from dataclasses import asdict
from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk
from md_generator.vector.exceptions import TenantBoundaryError
from md_generator.adapters.langchain.exceptions import LangChainDependencyError

try:
    from langchain_core.document_loaders import BaseLoader
    from langchain_core.documents import Document
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseLoader = object  # type: ignore[misc, assignment]
    Document = Any  # type: ignore[misc, assignment]
    _LANGCHAIN_AVAILABLE = False


def extract_semantic_key(model: Any) -> str:
    """Extracts canonical semantic_key from SemanticChunk or SemanticDocument without falling back to source_path."""
    if hasattr(model, "semantic_key") and getattr(model, "semantic_key"):
        return str(getattr(model, "semantic_key"))
    entities = getattr(model, "entities", None)
    if entities and len(entities) > 0:
        for ent in entities:
            if isinstance(getattr(ent, "metadata", None), dict) and "semantic_key" in ent.metadata:
                return str(ent.metadata["semantic_key"])
    meta = getattr(model, "metadata", None)
    if meta and hasattr(meta, "symbol_name") and meta.symbol_name:
        return str(meta.symbol_name)
    return ""


def resolve_tenant_id(explicit_tenant: Optional[str], model: Any) -> str:
    """Resolves tenant ID strictly without inferring from metadata.system.
    
    1. Extracts explicit tenant_id from model if present.
    2. Validates explicit loader tenant_id if provided.
    3. Rejects conflicts between loader tenant_id and model tenant_id.
    4. Raises TenantBoundaryError if unresolved (zero default fallback, zero metadata.system inference).
    """
    model_tenant = getattr(model, "tenant_id", None)
    if isinstance(model_tenant, str) and model_tenant.strip():
        model_tenant = model_tenant.strip()
    else:
        model_tenant = None

    exp_tenant = (
        explicit_tenant.strip()
        if (explicit_tenant and isinstance(explicit_tenant, str) and explicit_tenant.strip())
        else None
    )

    if exp_tenant and model_tenant and exp_tenant != model_tenant:
        raise TenantBoundaryError(
            f"Conflicting tenant identity: loader tenant_id '{exp_tenant}' "
            f"does not match model tenant_id '{model_tenant}'."
        )

    resolved = exp_tenant or model_tenant
    if not resolved:
        raise TenantBoundaryError(
            "Cannot load document without tenant identity. An explicit non-empty tenant_id "
            "must be provided to MDDocumentLoader, or the model must carry an explicit tenant_id. "
            "metadata.system denotes source platform and is NOT a tenant identifier."
        )
    return resolved


class MDDocumentLoader(BaseLoader if _LANGCHAIN_AVAILABLE else object):  # type: ignore[misc]
    """Loads SemanticDocument and SemanticChunks into LangChain Document instances without mutation.
    
    Implements LangChain BaseLoader's lazy_load() generator interface and inherits load().
    """

    def __init__(
        self,
        semantic_document: Optional[SemanticDocument] = None,
        chunks: Optional[List[SemanticChunk]] = None,
        tenant_id: Optional[str] = None,
    ):
        if semantic_document is None and (chunks is None or len(chunks) == 0):
            raise ValueError("MDDocumentLoader requires either a semantic_document or non-empty chunks list.")
        if tenant_id is not None and (not isinstance(tenant_id, str) or not tenant_id.strip()):
            raise TenantBoundaryError("When provided, tenant_id must be a non-empty string.")

        self.semantic_document = semantic_document
        self.chunks = list(chunks) if chunks is not None else None
        self.tenant_id = tenant_id.strip() if tenant_id else None

    def _convert_documents(self) -> Iterator[Any]:
        """Private generator yielding LangChain Document instances without mutating inputs."""
        if self.chunks is not None and len(self.chunks) > 0:
            for chunk in self.chunks:
                tenant = resolve_tenant_id(self.tenant_id, chunk)
                sem_key = extract_semantic_key(chunk)
                metadata: Dict[str, Any] = {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "tenant_id": tenant,
                    "semantic_key": sem_key,
                    "source_location": asdict(chunk.lineage.location) if chunk.lineage and chunk.lineage.location else None,
                    "security_classification": chunk.metadata.security_classification if chunk.metadata else "internal",
                    "entity_type": chunk.entities[0].entity_type if chunk.entities else None,
                    "parent_chunk_id": chunk.lineage.parent_chunk_id if chunk.lineage else None,
                }
                yield Document(
                    page_content=chunk.sanitized_content,
                    metadata=metadata,
                )
        elif self.semantic_document is not None:
            tenant = resolve_tenant_id(self.tenant_id, self.semantic_document)
            sem_key = extract_semantic_key(self.semantic_document)
            metadata = {
                "document_id": self.semantic_document.document_id,
                "chunk_id": None,
                "tenant_id": tenant,
                "semantic_key": sem_key,
                "source_location": asdict(self.semantic_document.metadata.source_location) if self.semantic_document.metadata and hasattr(self.semantic_document.metadata, "source_location") and self.semantic_document.metadata.source_location else None,
                "security_classification": self.semantic_document.metadata.security_classification if self.semantic_document.metadata else "internal",
                "document_type": self.semantic_document.document_type,
            }
            yield Document(
                page_content=self.semantic_document.sanitized_content,
                metadata=metadata,
            )

    def lazy_load(self) -> Iterator[Any]:
        """Generates LangChain Document instances lazily as required by BaseLoader.
        
        Raises LangChainDependencyError if langchain-core is not installed.
        Raises TenantBoundaryError if tenant identity cannot be resolved without defaulting or system inference.
        """
        if not _LANGCHAIN_AVAILABLE:
            raise LangChainDependencyError(
                "langchain-core is required to use MDDocumentLoader. "
                "Install it with 'pip install langchain-core'."
            )

        for document in self._convert_documents():
            yield document

    if not _LANGCHAIN_AVAILABLE:
        def load(self) -> List[Any]:
            """Fallback load method raising LangChainDependencyError when langchain-core is absent.
            
            When langchain-core is present, load() is inherited from BaseLoader and collects lazy_load().
            """
            raise LangChainDependencyError(
                "langchain-core is required to use MDDocumentLoader. "
                "Install it with 'pip install langchain-core'."
            )
