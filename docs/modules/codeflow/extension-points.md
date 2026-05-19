# Codeflow Extension Points

Language parsers under `codeflow/parsers/` and optional tree-sitter adapters.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
