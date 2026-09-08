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

## CLI Parameter Specification (`md-odata generate`)

| Parameter | Type | Default | Description / Choices |
|-----------|------|---------|-----------------------|
| `-f`, `--file` | `Path` | `None` | Path to single OData CSDL `$metadata` file (`.xml`, `.json`, `.edmx`) |
| `-d`, `--folder` | `Path` | `None` | Directory path containing OData CSDL files |
| `-z`, `--zip` | `Path` | `None` | ZIP archive path containing CSDL metadata files |
| `-u`, `--url` | `str` | `None` | Repeatable live `$metadata` URL to fetch OData specifications |
| `-o`, `--output` | `Path` | `./odata-out` | Output destination directory for generated Markdown catalogs |
| `--graph` | `flag` | `False` | Generate entity set relationship Mermaid diagrams & JSON graphs |
| `--chunk` | `flag` | `False` | Produce semantic JSONL chunks for RAG embedding pipelines |
| `--config` | `Path` | `None` | Path to single YAML configuration file |

## YAML Configuration Schema (`odata-export.yaml`)

```yaml
input:
  folder: ./metadata-exports
  urls: ["https://host/service/$metadata"]
output:
  path: ./odata-out
graph: true                            # Generate entity set relationship diagrams
chunk: true                            # Generate JSONL semantic chunks
```

## HTTP API & MCP Parameter Specifications

Env prefix **`ODATA_TO_MD_`**: `ODATA_TO_MD_HOST` (default `127.0.0.1`), `ODATA_TO_MD_PORT` (default **8017**), `ODATA_TO_MD_MAX_SYNC_ZIP_MB` (default `80`), `ODATA_TO_MD_CORS_ORIGINS`.

Routes (`md_generator.odata.api.main:app`):

- `GET /health`
- `POST /odata-to-md/generate` — Multipart `file` (CSDL `.xml`, `.json`, `.edmx`) + optional `options_json` form string → returns synchronous ZIP
- MCP tools (mounted at `/mcp` or stdio `md-odata-mcp`):
  - `odata_validate_metadata`: Validate CSDL V1-V4 XML/JSON schema
  - `odata_generate_readme_markdown`: Generate service catalog summary README
  - `odata_run_sync_zip_base64`: Execute full conversion and return base64 ZIP

## Primary entry points (from pyproject)

- `md-odata` — CLI (`md_generator.odata.cli.main:main`; subcommand `generate`)
- `md-odata-api` — FastAPI (`md_generator.odata.api.run:main`)
- `md-odata-mcp` — MCP (`md_generator.odata.api.mcp_server:main`)
- `mdengine odata-to-md generate …` — meta-router alias

## Core layout

- **Package:** `md_generator.odata`
- **Notable areas:** `cli`, `api`, `core`, `parser` (XML V1–V4, JSON V4), `writers`, `generators`, `chunking`, `fetch`

## Examples

Concrete commands: [references/example.md](references/example.md).

## See also

- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [OpenAPI skill](../mdengine-ai-openapi/SKILL.md) — OpenAPI specs (distinct from OData CSDL)
- [CLI reference](../mdengine-reference/SKILL.md)

