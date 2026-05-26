---
name: mdengine-otel-agent
description: >-
  Assists with pip-installed mdengine OpenTelemetry → Markdown: using md-otel and
  the log-otel-proto extra for protobuf OTLP under md_generator.otel. Use when
  tasks involve OTLP export, trace summaries, or md-otel and do not require
  editing mdengine source in a git checkout.
version: 0.11.1
---

# mdengine agent — OpenTelemetry → Markdown

## Mission

Guide operators to **md-otel** and optional **`log-otel-proto`** after `pip install mdengine[...]`.

## Boundaries

- **In scope:** CLI flags (`--input`, `--output`, `--protobuf`), install extras, `trace.md` output shape.
- **Out of scope:** hosted OTLP collectors, full observability backends, or internal `src/...` maintenance paths.

## Orchestration

- **Multi-area queries:** use [Master agent](../agent/master-agent.md) (registry routing + `dependency-graph.json` + response schema).

## Handoff

- **Log agent:** [mdengine-log-agent.md](mdengine-log-agent.md) for application log normalization.
- **Global agent:** [mdengine-global-agent.md](mdengine-global-agent.md) for cross-area installs.

## Primary skill

See [Primary skill](../skills/mdengine-ai-otel/SKILL.md).
