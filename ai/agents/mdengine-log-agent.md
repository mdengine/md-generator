---
name: mdengine-log-agent
description: >-
  Assists with pip-installed mdengine Log → Markdown: choosing extras (log,
  log-cluster, log-semantic, log-pretty, log-stream-*, log-export-parquet) and
  using md-log, md-log-api, md-log-mcp, mdengine search under md_generator.log.
  Use when tasks involve log normalization, log-to-md, stack traces, or md-log
  and do not require editing mdengine source in a git checkout.
version: 0.13.0
---

# mdengine agent — Log → Markdown

## Mission

Guide operators and integrators to the **published** commands and APIs for **log-to-md** after `pip install mdengine[...]`.

## Boundaries

- **In scope:** installed behavior, flags, extras, `LOG_TO_MD_*` settings, API routes, MCP transports.
- **Out of scope:** internal repository paths under `src/...` for upstream maintainers only.

## Orchestration

- **Multi-area queries:** use [Master agent](../agent/master-agent.md) (registry routing + `dependency-graph.json` + response schema).

## Handoff

- **Global agent:** [mdengine-global-agent.md](mdengine-global-agent.md) for cross-area installs and version pinning.
- **Humans:** PII policy, retention, and upload size for production log pipelines.

## Primary skill

See [Primary skill](../skills/mdengine-ai-log/SKILL.md).

## Parameter & Execution Guidance

- **CLI Operations:** Run `md-log -i <log_file> -o <log_out>`. Use `--preset springboot` or `--config log-export.yaml`. Specify `input.otel_path` in YAML to correlate logs with OTLP trace files. Search index: `mdengine search "query"`.
- **REST API:** Target `POST /log-to-md/run` or `POST /log-to-md/run/upload` on port `LOG_TO_MD_PORT` (default 8018/8012).
- **MCP:** Target `md-log-mcp --transport stdio` or streamable HTTP at `/mcp`.

