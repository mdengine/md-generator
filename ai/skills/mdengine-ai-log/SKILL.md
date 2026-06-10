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

- **Inputs:** Log files or directories (`--input`), YAML `--config`, optional `--preset` (e.g. `generic`, `springboot`). Async: `--async` with SQLite job store.
- **Outputs:** Markdown bundle / ZIP per config; **`md-log --help`** for full flags.

## Install

```bash
pip install "mdengine[log]"
```

Optional capability extras:

| Extra | Purpose |
|-------|---------|
| **`log-cluster`** | scikit-learn clustering helpers |
| **`log-semantic`** | SentenceTransformers / semantic grouping (heavy) |
| **`log-pretty`** | loguru pretty-print paths |
| **`log-export-parquet`** | Parquet export (`pyarrow`) |
| **`log-stream-kafka`** | Kafka ingest (`kafka-python`) |
| **`log-stream-redis`** | Redis stream ingest |
| **`log-stream-ws`** | WebSocket stream ingest |
| **`log-otel-proto`** | OTLP protobuf (shared with `md-otel`) |

```bash
pip install "mdengine[log,log-cluster,api,mcp]"
```

## Primary entry points (from pyproject)

- `md-log` — CLI (`md_generator.log.cli.main:main`)
- `md-log-api` — FastAPI (`md_generator.log.api.run:main`)
- `md-log-mcp` — MCP (`md_generator.log.api.mcp_server:main`)
- `mdengine log-to-md …` — meta-router alias
- `mdengine search "query" [--index PATH]` — hybrid BM25/vector search over exported log Markdown index (default index dir: `./log-docs`)

## Core layout

- **Package:** `md_generator.log`
- **Notable areas:** `cli`, `api`, `core`, `parser`, `config`, `search`, `streaming`, `incidents`, `chunking`

## HTTP API (summary)

Env prefix **`LOG_TO_MD_`**: `LOG_TO_MD_HOST`, `LOG_TO_MD_PORT` (default **8012**), `LOG_TO_MD_MAX_SYNC_ZIP_MB`, `LOG_TO_MD_MAX_LOG_UPLOAD_MB`, job SQLite / workspace paths.

Routes (`md_generator.log.api.main:app`):

- `GET /health`
- `POST /log-to-md/run` — JSON → sync ZIP
- `POST /log-to-md/run/upload` — multipart log + optional `config` JSON
- `POST /log-to-md/job` / `POST /log-to-md/job/upload` — async jobs
- `GET /log-to-md/job/{job_id}` — status
- `GET /log-to-md/job/{job_id}/download` — ZIP when complete
- `GET /log-to-md/job/{job_id}/events` — SSE progress
- MCP at **`/mcp`**

Full tables: [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md).

## See also

- [OpenTelemetry skill](../mdengine-ai-otel/SKILL.md) — trace export (complementary)
- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)
