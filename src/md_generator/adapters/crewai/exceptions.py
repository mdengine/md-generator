"""Standalone exception hierarchy for mdengine CrewAI tool adapters.

Uncoupled from vector store errors and LangGraph errors, while preserving
direct propagation of the shared TenantBoundaryError for security violations.
"""

from md_generator.vector.exceptions import TenantBoundaryError

__all__ = [
    "CrewAIAdapterError",
    "CrewAIDependencyError",
    "CrewAIToolExecutionError",
    "TenantBoundaryError",
]


class CrewAIAdapterError(Exception):
    """Base exception for all CrewAI adapter operations."""
    pass


class CrewAIDependencyError(ImportError, CrewAIAdapterError):
    """Raised when CrewAI is installed but cannot be imported due to syntax or dependency errors."""
    pass


class CrewAIToolExecutionError(CrewAIAdapterError):
    """Raised on invalid document scores, execution failures, or tool operational faults."""
    pass
