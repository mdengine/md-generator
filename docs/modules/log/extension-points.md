# Log Analysis Extension Points

Presets in `log/config/presets/`; pipeline stages under ingestion, parsing, clustering.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
