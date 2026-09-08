---
name: mdengine-ai-log
description: "Documents pip-installed mdengine features for Log → Markdown: extras, CLIs, and public imports under md_generator.log. Use when the user mentions `md-log`, `md-log-api`, `md-log-mcp`, log normalization, stack traces, or needs this capability after installing mdengine from PyPI. Package summary: log-to-md — normalize logs to AI-oriented Markdown (presets, clustering, search, streaming, API/MCP)."
version: 0.13.0
---
# mdengine — Log → Markdown (log-to-md)

<!-- Prefer editing references/example.md for copy-paste snippets. -->

## Purpose

log-to-md: parse and normalize application logs into structured Markdown (timelines, incidents, clustering when optional extras are installed). After export, search indexed chunks with **`mdengine search`**.

## Input / output

## CLI Parameter Specification (`md-log`)

| Parameter | Type | Default | Description / Choices |
|-----------|------|---------|-----------------------|
| `-i`, `--input` | `Path` | Positional / Flag | Path to log file or directory of logs |
| `-o`, `--output` | `Path` | `./log-out` | Target output directory for normalized Markdown |
| `--config` | `Path` | `None` | Path to YAML log export configuration file |
| `--preset` | `str` | `generic` | Log format preset: `generic`, `springboot`, `syslog`, `nginx`, `json`, `otlp` |
| `--async` | `flag` | `False` | Process log conversion asynchronously via SQLite job store |

## YAML Configuration Schema (`log-export.yaml`)

```yaml
input:
  path: ./logs
  preset: springboot                    # generic, springboot, syslog, nginx, json
  otel_path: ./otel-traces             # Directory of OTLP trace files for log-span correlation
output:
  path: ./log-out
  split_files: true
clustering:
  enabled: true                        # Requires log-cluster extra (scikit-learn)
  max_clusters: 20
search_index:
  build_index: true                    # Build BM25/vector search index for `mdengine search`
```

## Primary entry points (from pyproject)

- `md-log` — CLI (`md_generator.log.cli.main:main`)
- `md-log-api` — FastAPI (`md_generator.log.api.run:main`)
- `md-log-mcp` — MCP (`md_generator.log.api.mcp_server:main`)
- `mdengine log-to-md …` — meta-router alias
- `mdengine search "query" [--index PATH]` — search exported log Markdown index (default dir: `./log-docs`)

## Core layout

- **Package:** `md_generator.log`
- **Notable areas:** `cli`, `api`, `core`, `parser`, `config`, `search`, `streaming`, `incidents`, `chunking`

## HTTP API & MCP Parameter Specifications

Env prefix **`LOG_TO_MD_`**: `LOG_TO_MD_HOST` (default `127.0.0.1`), `LOG_TO_MD_PORT` (default **8018** / **8012**), `LOG_TO_MD_MAX_SYNC_ZIP_MB` (default `64`), `LOG_TO_MD_MAX_LOG_UPLOAD_MB` (default `200`), job SQLite / workspace paths.

Routes (`md_generator.log.api.main:app`):

- `GET /health`
- `POST /log-to-md/run` — JSON body matching `LogToMdRunBody` → returns synchronous ZIP
- `POST /log-to-md/run/upload` — Multipart `file` + optional `config` JSON string → returns synchronous ZIP
- `POST /log-to-md/job` / `POST /log-to-md/job/upload` — Async job endpoints → `{ "job_id": "<id>" }`
- `GET /log-to-md/job/{job_id}` — Status & progress metrics JSON
- `GET /log-to-md/job/{job_id}/download` — Download ZIP artifact bundle
- `GET /log-to-md/job/{job_id}/events` — SSE progress event stream
- MCP endpoint at **`/mcp`** or stdio binary `md-log-mcp`

## See also

- [OpenTelemetry skill](../mdengine-ai-otel/SKILL.md) — trace export (complementary)
- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)

