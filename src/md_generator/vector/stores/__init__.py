"""Vector store adapters package for md-generator vector module."""

from md_generator.vector.stores.base import BaseVectorStore, StoreRegistry
from md_generator.vector.stores.in_memory import InMemoryVectorStore

__all__ = [
    "BaseVectorStore",
    "StoreRegistry",
    "InMemoryVectorStore",
]
