# OpenTelemetry Traces Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--input` | Path | optional | — | — | — |
| `--output` | Path | optional | Path('./otel-docs') | — | — |
| `--protobuf` | flag | optional | false | — | — |


## API routes (HTTP parameters)

_No entries detected._


## Environment variables

_No entries detected._


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

_No entries detected._


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `log-otel-proto for protobuf`.
