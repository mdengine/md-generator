"""Neo4j GraphStore backend stub — implement when enterprise deployment requires a driver."""

from __future__ import annotations

from md_generator.sap.graph.backends.memory import InMemoryGraphStore


class Neo4jGraphStoreStub(InMemoryGraphStore):
    """Placeholder: persists via in-memory store until neo4j driver is added."""

    backend_name = "neo4j"
