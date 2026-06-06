# OData Metadata Extension Points

Parsers under `odata/parser/`; namespace and relationship graph in `odata/core/`.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
