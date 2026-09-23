"""Vector embedding and vector store infrastructure package for md-generator."""

from md_generator.vector.exceptions import (
    VectorError,
    EmbeddingProviderError,
    VectorStoreError,
    CollectionConfigurationError,
    VectorDimensionMismatchError,
    VectorValueError,
    TenantBoundaryError,
)
from md_generator.vector.model import (
    EmbeddingRecord,
    VectorQueryResult,
    CollectionConfig,
    VectorSyncRecord,
    VectorSyncManifest,
    VectorSyncManifestStore,
    validate_vector,
    manifest_document_key,
    manifest_record_key,
)
from md_generator.vector.processor import (
    EmbeddingProcessor,
    VectorSyncResult,
    compute_embedding_processing_fingerprint,
    compute_embedding_id,
)

__all__ = [
    "VectorError",
    "EmbeddingProviderError",
    "VectorStoreError",
    "CollectionConfigurationError",
    "VectorDimensionMismatchError",
    "VectorValueError",
    "TenantBoundaryError",
    "EmbeddingRecord",
    "VectorQueryResult",
    "CollectionConfig",
    "VectorSyncRecord",
    "VectorSyncManifest",
    "VectorSyncManifestStore",
    "validate_vector",
    "manifest_document_key",
    "manifest_record_key",
    "EmbeddingProcessor",
    "VectorSyncResult",
    "compute_embedding_processing_fingerprint",
    "compute_embedding_id",
]
