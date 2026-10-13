"""Standalone exception hierarchy for md-generator Knowledge Graph and GraphRAG layer."""

from md_generator.vector.exceptions import TenantBoundaryError

__all__ = [
    "GraphError",
    "Neo4jDependencyError",
    "GraphStoreError",
    "GraphQueryError",
    "TenantBoundaryError",
]


class GraphError(Exception):
    """Base exception for all knowledge graph and GraphRAG operations."""
    pass


class Neo4jDependencyError(ImportError, GraphError):
    """Raised when neo4j optional package is missing, broken, or fails to initialize."""
    pass


class GraphStoreError(GraphError):
    """Raised on graph storage, connection, persistence, or transaction faults."""
    pass


class GraphQueryError(GraphError):
    """Raised on invalid Cypher queries, traversal parameters, cycle limits, or traversal budget overflows."""
    pass
