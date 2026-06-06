# `md_generator.otel` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert OTLP JSON or protobuf trace exports to Trace summary Markdown (`trace.md`) |
| CLI | `md-otel` |
| Extra | `log-otel-proto for protobuf` |
| Tier | `simple` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--input` | Path | optional | — | — | — |
| `--output` | Path | optional | Path('./otel-docs') | — | — |
| `--protobuf` | flag | optional | false | — | — |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| load_otlp_json | callable | — |
| load_otlp_bytes | callable | — |
| parse_otlp_spans | callable | — |


## Python API (mkdocstrings)

::: md_generator.otel
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
