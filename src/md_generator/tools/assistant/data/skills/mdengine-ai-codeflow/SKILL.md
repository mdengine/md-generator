---
name: mdengine-ai-codeflow
description: "Documents pip-installed mdengine features for Codeflow (code → Markdown): extras, CLIs, and public imports under md_generator.codeflow. Use when the user mentions `codeflow`, `md-codeflow`, tree-sitter parsers, architecture graphs, or needs this capability after installing mdengine from PyPI. Package summary: Multi-language execution flow extraction → Markdown, Mermaid, graph JSON, HTML."
version: 0.13.0
---
# mdengine — Code → architecture Markdown (codeflow)

<!-- Prefer editing references/example.md for copy-paste snippets. -->

## Purpose

codeflow: scan repositories and extract execution-flow / architecture artifacts into Markdown, Mermaid diagrams, graph JSON, and HTML reports. Supports heuristic parsers plus optional Tree-sitter and libclang backends.

## Install

```bash
pip install "mdengine[codeflow]"
```

Optional extras:

| Extra | Purpose |
|-------|---------|
| **`codeflow-treesitter`** | Tree-sitter parsers (JS/TS, Python, Java, Go, C/C++, Rust, Kotlin, C#, Swift, Ruby, Lua, Scala, Zig, PHP, …) |
| **`codeflow-clang`** | libclang for C/C++ precision |
| **`codeflow-semantic`** | Embeddings + semantic clustering (heavy) |
| **`codeflow-worker`** | Celery + Redis horizontal workers for API jobs |

```bash
pip install "mdengine[codeflow,codeflow-treesitter,api,mcp]"
```

## CLI Parameter Specification (`md-codeflow scan` / `codeflow scan`)

| Parameter | Type | Default | Description / Choices |
|-----------|------|---------|-----------------------|
| `project_root` | `Path` | Positional | Path to the source code directory to scan |
| `-o`, `--output` | `Path` | Required | Target output directory for scan artifacts |
| `-l`, `--lang` | `str` | Auto | Language override: `java`, `python`, `js`, `ts`, `cpp`, `go`, `php`, `rust`, etc. |
| `--formats` | `str` | `md,mermaid,json,html` | Comma-separated output formats: `md`, `mermaid`, `json`, `html` |
| `--journey-format` | `str` | `None` | Cross-file journey export formats: `md`, `json`, `mermaid`, `html`, `dot`, `graphml`, `gexf` |
| `--parser-mode` | `str` | `default` | Parser mode: `default` (heuristic AST), `treesitter` (tree-sitter grammar), `clang` (libclang for C/C++) |
| `--entry` | `str` | `None` | Comma-separated entry point symbol IDs |
| `--entries-file` | `Path` | `None` | File containing one entry point symbol per line (`#` comments allowed) |
| `--emit-entry-per-method` | `flag` | `False` | Emit separate method slice output directory under `methods/<slug>/` |
| `--emit-entry-max` | `int` | `10000` | Volume cap on emitted method slice directories when `--emit-entry-per-method` is set |
| `--entry-fallback` | `str` | `roots` | Entry fallback strategy when no entry points detected: `none`, `roots` (in-degree 0), `first_n` |
| `--entry-fallback-max` | `int` | `100` | Maximum fallback entry symbols to evaluate |
| `--emit-cfg` | `flag` | `False` | Build Control Flow Graph IR and write `cfg.json`, `cfg.mmd`, and flow CFG section |
| `--cfg-max-nodes` | `int` | `500` | Node limit cap for Control Flow Graph generation |
| `--emit-graph-schema` | `flag` | `False` | Export stable `graph-schema.json` Node/Edge view with file/class CONTAINS edges |
| `--intelligence-list-cap` | `int` | `80` | Maximum Called By and Impact items to include per method Markdown doc |
| `--no-scan-summary` | `flag` | `False` | Disable writing root `scan-summary.md` report |

## YAML Configuration Schema (`codeflow-scan.yaml`)

```yaml
project_root: ./src
output_path: ./codeflow-out
languages: ["java", "python"]
formats: ["md", "mermaid", "json", "html"]
journey_formats: ["md", "json", "dot", "graphml", "gexf"]
parser_mode: treesitter
entry:
  symbols: ["com.example.service.OrderService.createOrder"]
  fallback: roots
  fallback_max: 50
cfg:
  enabled: true
  max_nodes: 500
output_options:
  emit_entry_per_method: true
  emit_entry_max: 1000
  intelligence_list_cap: 80
  emit_graph_schema: true
```

## Primary entry points (from pyproject)

- `md-codeflow` / `codeflow` — CLI (`md_generator.codeflow.cli.main:main`)
- `md-codeflow-api` — FastAPI (`md_generator.codeflow.api.run:main`)
- `md-codeflow-mcp` — MCP (`md_generator.codeflow.api.mcp_server:main`)
- `mdengine codeflow-to-md scan …` — meta-router alias

## Core layout

- **Package:** `md_generator.codeflow`
- **Notable areas:** `cli`, `api`, `parsers` (heuristic, treesitter, clang), `journey` (graph_export: dot, graphml, gexf), `lang_dispatch`, `graph`, `generators`, `ingestion`, `worker`

## HTTP API & MCP Parameter Specification

Env prefix **`CODEFLOW_TO_MD_`** / **`CODEFLOW_`**: `CODEFLOW_TO_MD_HOST` (default `127.0.0.1`), `CODEFLOW_TO_MD_PORT` (default **8016**), `CODEFLOW_MAX_UPLOAD_ZIP_MB` (default `256`), `CODEFLOW_MAX_SYNC_ZIP_MB` (default `64`), `CODEFLOW_JOB_WORKSPACE_ROOT`, `CODEFLOW_SQLITE_PATH`, `CODEFLOW_CORS`.

Routes (`md_generator.codeflow.api.main:app`):

- `GET /health`
- `POST /codeflow-to-md/scan` — Upload ZIP or workspace JSON config → returns synchronous scan ZIP
- `POST /codeflow-to-md/job` — Create background workspace scan job → returns `{ "job_id": "<id>" }`
- `GET /codeflow-to-md/job/{job_id}` — Job status and progress metrics
- `GET /codeflow-to-md/job/{job_id}/download` — Download scan result ZIP
- MCP endpoint at **`/mcp`** (Streamable HTTP MCP) or stdio binary `md-codeflow-mcp`

## Examples

Concrete commands: [references/example.md](references/example.md).

## See also

- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)

