# OpenTelemetry Traces Module Overview

## Purpose

The **OpenTelemetry Traces** module (`md_generator.otel`) converts **OTLP JSON or protobuf trace exports** into **Trace summary Markdown (`trace.md`)**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from OTLP JSON or protobuf trace exports into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from OTLP JSON or protobuf trace exports.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `log-otel-proto for protobuf` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.otel` |
| Source tree | `src/md_generator/otel` |
| CLI | `md-otel` |
| Alternate CLI | `mdengine otel-to-md` |
| PyPI extra | `log-otel-proto for protobuf` |
| Complexity tier | `simple` |
| API service name | `(none)` |

## Primary entry points

- `load_otlp_json`
- `load_otlp_bytes`
- `parse_otlp_spans`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[otel_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


