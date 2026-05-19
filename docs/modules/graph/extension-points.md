# Graph Metadata Extension Points

Graph adapters: `graph/adapters/neo4j_adapter.py`, `networkx_adapter.py`.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
