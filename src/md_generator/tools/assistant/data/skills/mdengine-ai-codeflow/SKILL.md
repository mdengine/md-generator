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

## Primary entry points (from pyproject)

- `md-codeflow` / `codeflow` — CLI (`md_generator.codeflow.cli.main:main`)
- `md-codeflow-api` — FastAPI (`md_generator.codeflow.api.run:main`)
- `md-codeflow-mcp` — MCP (`md_generator.codeflow.api.mcp_server:main`)
- `mdengine codeflow-to-md scan …` — meta-router alias

## Input / output

- **Inputs:** Source trees, scan configs, YAML; subcommands vary — start with **`md-codeflow --help`** or **`md-codeflow scan --help`**.
- **Outputs:** Markdown bundles, Mermaid, `graph.json`, HTML per config.

## Core layout

- **Package:** `md_generator.codeflow`
- **Notable areas:** `cli`, `api`, `parsers`, `lang_dispatch`, `graph`, `generators`, `ingestion`, `worker`

## Examples

Concrete commands: [references/example.md](references/example.md).

## See also

- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)
