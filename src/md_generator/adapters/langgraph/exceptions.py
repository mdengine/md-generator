"""LangGraph adapter standalone exception hierarchy.

Uncoupled from vector-domain errors to prevent unrelated graph failures
from being caught as vector store or embedding provider errors.
"""

from md_generator.vector.exceptions import TenantBoundaryError

__all__ = [
    "LangGraphAdapterError",
    "LangGraphDependencyError",
    "GraphStateValidationError",
    "GraphRoutingError",
    "TenantBoundaryError",
]


class LangGraphAdapterError(Exception):
    """Base exception for all LangGraph adapter operations."""
    pass


class LangGraphDependencyError(ImportError, LangGraphAdapterError):
    """Raised when langgraph is required but not installed."""
    pass


class GraphStateValidationError(LangGraphAdapterError):
    """Raised when graph state violates schema, typing, or serialization constraints."""
    pass


class GraphRoutingError(LangGraphAdapterError):
    """Raised when conditional routing fails to evaluate a valid branch or encounters invalid document scores."""
    pass
