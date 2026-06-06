# OpenTelemetry Traces Extension Points

Lightweight CLI exporter; protobuf path uses optional `log-otel-proto` extra.

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
