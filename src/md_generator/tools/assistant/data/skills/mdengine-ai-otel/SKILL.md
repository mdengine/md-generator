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

- **Inputs:** `--input` OTLP file; `--protobuf` when the file is protobuf-encoded OTLP.
- **Outputs:** `--output` directory (default `./otel-docs`) containing **`trace.md`**. **`md-otel --help`** for flags.

## Examples

Concrete commands: [references/example.md](references/example.md).

## Install

JSON OTLP (uses shared log I/O helpers):

```bash
pip install mdengine
```

Protobuf OTLP requires the optional extra:

```bash
pip install "mdengine[log-otel-proto]"
```

## Primary entry points (from pyproject)

- `md-otel` — CLI (`md_generator.otel.cli.main:main`)
- `mdengine otel-to-md …` — meta-router alias

There is **no** separate `md-otel-api` / `md-otel-mcp` script in `pyproject.toml`; integration is CLI-only today.

## Core layout

- **Package:** `md_generator.otel`
- **Modules:** `otel_parser` (load OTLP JSON/bytes), `otel_spans` (span extraction)

## Related extras

- **`log-otel-proto`** — `opentelemetry-proto` + `protobuf` for `--protobuf` ingest (shared with log pipeline tooling).

## See also

- [Log → Markdown](../mdengine-ai-log/SKILL.md) — log normalization (complementary to traces)
- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)
