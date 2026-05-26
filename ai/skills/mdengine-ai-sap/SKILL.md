---
name: mdengine-ai-sap
description: "Documents pip-installed mdengine features for SAP → Markdown: extras, CLIs, and public imports under md_generator.sap. Use when the user mentions `md-sap`, `md-sap-api`, `md-sap-mcp`, ABAP, CDS, DDIC, or needs this capability after installing mdengine from PyPI. Package summary: sap-to-md — export SAP artifacts to AI-oriented Markdown (parsers, lineage, governance, ZIP/API/MCP)."
version: 0.11.1
---
# mdengine — SAP → Markdown (sap-to-md)

<!-- Prefer editing references/example.md for copy-paste snippets. -->

## Purpose

sap-to-md: extract SAP source trees (ABAP, optional CDS/DDIC parsers) into structured Markdown bundles with optional relationship graphs, chunking, lineage, and governance analyzers.

## Input / output

- **Inputs:** SAP source paths (files or directories), YAML `--config`, feature include/exclude lists, parser toggles (`--include-cds`, `--include-ddic`, …).
- **Outputs:** Markdown directory or ZIP per config; async jobs with `--async`. **`md-sap --help`** for full flags.

## Examples

Concrete commands: [references/example.md](references/example.md).

## Install

```bash
pip install "mdengine[sap]"
```

For HTTP API and MCP:

```bash
pip install "mdengine[sap,api,mcp]"
```

## Primary entry points (from pyproject)

- `md-sap` — CLI (`md_generator.sap.cli.main:main`)
- `md-sap-api` — FastAPI (`md_generator.sap.api.run:main`)
- `md-sap-mcp` — MCP (`md_generator.sap.api.mcp_server:main`)
- `mdengine sap-to-md …` — meta-router alias

## Core layout

- **Package:** `md_generator.sap`
- **Notable areas:** `cli`, `api` (FastAPI + MCP mount `/mcp`), `core` (extractor, jobs, zip export), `core/features`

## HTTP API (summary)

Env prefix **`SAP_TO_MD_`** (see `SapApiSettings`): `SAP_TO_MD_HOST`, `SAP_TO_MD_PORT` (default **8020**), `SAP_TO_MD_MAX_SYNC_ZIP_MB`, `SAP_TO_MD_JOB_SQLITE_PATH`, `SAP_TO_MD_JOB_WORKSPACE_ROOT`, `SAP_TO_MD_CORS_ORIGINS`.

Routes (FastAPI app `md_generator.sap.api.main:app`):

- `GET /health`
- `POST /sap-to-md/run` — JSON body → synchronous ZIP (`application/zip`)
- `POST /sap-to-md/job` — async job → `{ "job_id" }`
- `GET /sap-to-md/job/{job_id}` — status
- `GET /sap-to-md/job/{job_id}/download` — ZIP when `COMPLETED`
- MCP mounted at **`/mcp`** when using the HTTP app

Full tables alongside other services: [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md).

## APIs / MCP

See [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md). Install **`mdengine[api,mcp]`** plus **`mdengine[sap]`**.

## See also

- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)
