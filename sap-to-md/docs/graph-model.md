# Graph model

## Core types

- **GraphNode** — artifact, column, dataset, transformation node
- **GraphEdge** — typed relationship with optional column metadata
- **ArtifactGraph** — merged graph for one run
- **ArtifactGraphStore** / **InMemoryGraphStore** — implements `GraphStore` protocol; accumulates parser fragments
- **GraphStore protocol** — `graph/backends/protocol.py`; swap backends (Neo4j/Arango stubs in `graph/backends/`)

## RelationshipType taxonomy

Structural (`DEPENDS_ON`, `CONTAINS`, `REFERENCES`), data flow (`READS_FROM`, `TRANSFORMS`, `JOINS`, …), lineage (`DERIVES_FROM`, `MAPS_TO`), API (`EXPOSES`, `SERVES`), code (`CALLS`, `INCLUDES`), cross-system (`SAME_AS`, `EQUIVALENT_TO`).

Legacy `graph/relations.py` constants map via `graph/taxonomy.py`.

## NetworkX adapter

`graph/adapters/networkx.py` converts between `ArtifactGraph` and `nx.MultiDiGraph` for backward compatibility with v1 `build_sap_graph()`.
