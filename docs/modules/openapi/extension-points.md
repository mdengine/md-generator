# OpenAPI Extension Points

Pipeline: loaders, parsers, resolvers, generators, writers.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
