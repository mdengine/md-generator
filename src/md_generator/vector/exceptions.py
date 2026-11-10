"""Standardized vector exception hierarchy for md-generator vector infrastructure."""

class VectorError(Exception):
    """Base exception for all vector module operations."""
    pass


class EmbeddingProviderError(VectorError):
    """Raised when an embedding provider fails to generate vector embeddings."""
    pass


class VectorStoreError(VectorError):
    """Raised when a vector store fails an operation."""
    pass


class CollectionConfigurationError(VectorError):
    """Raised when vector collection settings or dimensions mismatch."""
    pass


class VectorDimensionMismatchError(VectorError):
    """Raised when input vector dimension does not match collection dimension."""
    pass


class VectorValueError(VectorError):
    """Raised when vector contains non-finite float values (NaN, +Inf, -Inf), zero magnitude, booleans, or malformed data."""
    pass


class TenantBoundaryError(VectorError):
    """Raised when a tenant isolation boundary constraint is violated."""
    pass
