---
name: mdengine-ai-odata
description: "Documents pip-installed mdengine features for OData → Markdown: extras, CLIs, and public imports under md_generator.odata. Use when the user mentions `md-odata`, `md-odata-api`, `md-odata-mcp`, CSDL, $metadata, or needs this capability after installing mdengine from PyPI. Package summary: odata-to-md — parse OData CSDL metadata (V1–V4, XML/JSON) into Markdown catalogs with optional graph and chunks."
version: 0.13.0
---
# mdengine — OData → Markdown (odata-to-md)

<!-- Prefer editing references/example.md for copy-paste snippets. -->

## Purpose

odata-to-md: ingest OData **$metadata** (CSDL XML/JSON, local files, folders, ZIP archives, or live URLs) and emit an AI-oriented Markdown knowledge pack (entity catalog, relationships, optional Mermaid graph and semantic chunks).

## Input / output

- **Inputs:** `--file`, `--folder`, or `--zip` for on-disk metadata; repeatable `--url` to fetch `$metadata`; optional YAML `--config`. Subcommand: **`generate`**.
- **Outputs:** Markdown directory (default under configured `output_path`); API returns a **ZIP** bundle. Flags: `--graph`, `--chunk`. **`md-odata generate --help`** for full flags.

## Examples

Concrete commands: [references/example.md](references/example.md).

## Install

```bash
pip install "mdengine[odata]"
```

For HTTP API and MCP:

```bash
pip install "mdengine[odata,api,mcp]"
```

## Primary entry points (from pyproject)

- `md-odata` — CLI (`md_generator.odata.cli.main:main`; subcommand `generate`)
- `md-odata-api` — FastAPI (`md_generator.odata.api.run:main`)
- `md-odata-mcp` — MCP (`md_generator.odata.api.mcp_server:main`)
- `mdengine odata-to-md generate …` — meta-router alias

## Core layout

- **Package:** `md_generator.odata`
- **Notable areas:** `cli`, `api` (FastAPI + MCP mount `/mcp`), `core` (extractor, run config, zip export), `parser` (XML V1–V4, JSON V4), `writers`, `generators`, `chunking`, `fetch`

## HTTP API (summary)

Env prefix **`ODATA_TO_MD_`** (see `OdataToMdSettings`): `ODATA_TO_MD_HOST`, `ODATA_TO_MD_PORT` (default **8017**), `ODATA_TO_MD_MAX_SYNC_ZIP_MB` (default **80**), `ODATA_TO_MD_CORS_ORIGINS`.

Routes (FastAPI app `md_generator.odata.api.main:app`):

- `GET /health`
- `POST /odata-to-md/generate` — multipart **`file`** (`.xml`, `.json`, `.edmx`) + optional **`options_json`** (form field) → synchronous ZIP (`application/zip`)

MCP is mounted at **`/mcp`** on the same app. Standalone MCP tools: `odata_validate_metadata`, `odata_generate_readme_markdown`, `odata_run_sync_zip_base64`.

Full tables alongside other services: [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md).

## APIs / MCP

See [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md). Install **`mdengine[api,mcp]`** plus **`mdengine[odata]`**.

## See also

- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [OpenAPI skill](../mdengine-ai-openapi/SKILL.md) — OpenAPI specs (distinct from OData CSDL)
- [CLI reference](../mdengine-reference/SKILL.md)
