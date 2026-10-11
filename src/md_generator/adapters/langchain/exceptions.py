"""Exceptions for LangChain adapter interoperability layer."""


class LangChainAdapterError(Exception):
    """Base exception for all LangChain adapter operations."""
    pass


class LangChainDependencyError(LangChainAdapterError, ImportError):
    """Raised when langchain-core is required for an adapter operation but not installed."""
    pass
