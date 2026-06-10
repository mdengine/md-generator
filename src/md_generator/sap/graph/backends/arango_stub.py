"""ArangoDB GraphStore backend stub — implement when hybrid graph/document store is needed."""

from __future__ import annotations

from md_generator.sap.graph.backends.memory import InMemoryGraphStore


class ArangoGraphStoreStub(InMemoryGraphStore):
    """Placeholder: persists via in-memory store until python-arango is added."""

    backend_name = "arango"
