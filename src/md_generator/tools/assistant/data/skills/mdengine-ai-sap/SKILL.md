---
name: mdengine-ai-sap
description: "Documents pip-installed mdengine features for SAP → Markdown: extras, CLIs, and public imports under md_generator.sap. Use when the user mentions `md-sap`, `md-sap-api`, `md-sap-mcp`, ABAP, CDS, DDIC, HANA, BW, Datasphere, or needs this capability after installing mdengine from PyPI. Package summary: sap-to-md — export SAP artifacts to AI-oriented Markdown (multi-parser pipeline, lineage, governance, ZIP/API/MCP)."
version: 0.13.0
---
# mdengine — SAP → Markdown (sap-to-md)

<!-- Prefer editing references/example.md for copy-paste snippets. -->

## Purpose

sap-to-md: discover and parse SAP-related source trees into structured Markdown knowledge packs with optional relationship graphs, semantic chunks, lineage, and governance analyzers. Supports legacy pipeline (v1) and canonical graph pipeline (v2).

## Parser coverage (auto-discovery)

File discovery recognizes (non-exhaustive):

| Domain | Examples |
|--------|----------|
| **ABAP** | `.abap`, `.prog`, `.asprog`, `.inc` |
| **CDS** | `.ddls`, `.cds`, `.ddlx` |
| **DDIC** | abapGit `.tabl.xml`, ADT `.ddl`, `.dd02l`/`.dd03l` exports |
| **HANA** | calculation / analytic / attribute views (`.calculationview`, `.hdbview`, …) |
| **BW** | ADSO, DTP, InfoObject, composite provider artifacts |
| **Datasphere** | views, data flows, analytical models |
| **OData in SAP context** | `$metadata.xml`, `.edmx`, embedded OData JSON; CLI **`--odata-url`** |
| **BAPI / IDoc / transport** | `.bapi.json`, `.idoc`, transport files |

For **standalone OData CSDL** catalogs (not SAP repo export), use [OData skill](../mdengine-ai-odata/SKILL.md) (`md-odata`).

## Feature flags (`--include` / `--exclude`)

Built-in features: `entities`, `technical`, `functional`, `relationships`, `lineage`, `governance`, `authorization`, `validations`, `graphs`, `chunks`, `json_output`, `odata_catalog`.

## Input / output

- **Inputs:** SAP source paths (files or directories), YAML `--config`, `--odata-url` (repeatable), feature include/exclude lists, parser toggles (`--include-cds`, `--include-ddic`), `--pipeline-version` (1=legacy, 2=canonical+graph), `--workers`.
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
- **Notable areas:** `cli`, `api`, `core` (extractor, jobs, features), `parser` (abap, cds, ddic, hana, bw, datasphere, odata, …), `markdown`, `orchestration`, `lineage`, `graph`

## HTTP API (summary)

Env prefix **`SAP_TO_MD_`**: `SAP_TO_MD_HOST`, `SAP_TO_MD_PORT` (default **8020**), `SAP_TO_MD_MAX_SYNC_ZIP_MB`, `SAP_TO_MD_JOB_SQLITE_PATH`, `SAP_TO_MD_JOB_WORKSPACE_ROOT`, `SAP_TO_MD_CORS_ORIGINS`.

Routes (`md_generator.sap.api.main:app`):

- `GET /health`
- `POST /sap-to-md/run` — JSON → synchronous ZIP
- `POST /sap-to-md/job` — async job → `{ "job_id" }`
- `GET /sap-to-md/job/{job_id}` — status
- `GET /sap-to-md/job/{job_id}/download` — ZIP when `COMPLETED`
- MCP at **`/mcp`**

Full tables: [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md).

## See also

- [OData skill](../mdengine-ai-odata/SKILL.md) — dedicated CSDL/$metadata export
- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)
