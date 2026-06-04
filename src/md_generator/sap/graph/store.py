"""Graph store — use InMemoryGraphStore or GraphStore protocol."""

from md_generator.sap.graph.backends.memory import ArtifactGraphStore, InMemoryGraphStore

__all__ = ["ArtifactGraphStore", "InMemoryGraphStore"]
