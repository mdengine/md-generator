# Log Analysis Extension Points

Presets in `log/config/presets/`; subcommands `md-log stream` and `md-log presets`; stages under ingestion, parsing, clustering, knowledge_graph, incremental, streaming, noise_reduction.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
