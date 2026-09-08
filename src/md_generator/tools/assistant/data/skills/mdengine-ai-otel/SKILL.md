---
name: mdengine-ai-otel
description: "Documents pip-installed mdengine features for OpenTelemetry → Markdown: CLIs and public imports under md_generator.otel. Use when the user mentions `md-otel`, OTLP, OpenTelemetry traces, or needs trace export after installing mdengine from PyPI. Package summary: otel-to-md — OTLP JSON/protobuf → Markdown trace summaries."
version: 0.11.1
---
# mdengine — OpenTelemetry → Markdown (otel-to-md)

<!-- Prefer editing references/example.md for copy-paste snippets. -->

## Purpose

otel-to-md: load OTLP export files (JSON or protobuf) and write a concise Markdown trace summary (`trace.md`) listing spans (trace/span IDs, service names).

## Input / output

## CLI Parameter Specification (`md-otel`)

| Parameter | Type | Default | Description / Choices |
|-----------|------|---------|-----------------------|
| `-i`, `--input` | `Path` | Positional / Flag | Path to OTLP trace export file (JSON or binary protobuf) |
| `-o`, `--output` | `Path` | `./otel-docs` | Target output directory for generated `trace.md` |
| `--protobuf` | `flag` | `False` | Decode input as binary OTLP protobuf format (requires `log-otel-proto` extra) |

## Install

JSON OTLP trace ingest:

```bash
pip install mdengine
```

Protobuf OTLP ingest requires the protobuf extra:

```bash
pip install "mdengine[log-otel-proto]"
```

## Primary entry points (from pyproject)

- `md-otel` — CLI (`md_generator.otel.cli.main:main`)
- `mdengine otel-to-md …` — meta-router alias

There is **no** separate `md-otel-api` / `md-otel-mcp` script in `pyproject.toml`; trace export is handled via CLI or correlated with logs via `input.otel_path` in `md-log`.

## Core layout

- **Package:** `md_generator.otel`
- **Modules:** `otel_parser` (`load_otlp_json`, `load_otlp_protobuf`), `otel_spans` (`parse_otlp_spans`)

## See also

- [Log → Markdown](../mdengine-ai-log/SKILL.md) — log normalization (complementary to traces)
- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)

