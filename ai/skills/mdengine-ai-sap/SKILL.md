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

## Parser coverage & Features (auto-discovery)

File discovery recognizes:

| Domain | File Extensions / Patterns |
|--------|----------------------------|
| **ABAP** | `.abap`, `.prog`, `.asprog`, `.inc`, `.clas.abap`, `.fugr.abap` |
| **ABAP Execution Journeys** | Static caller-callee call graphs (`abap_journey` engine, `CallExtractors` for `CALL FUNCTION`, `CALL METHOD`, `PERFORM`, `SELECT`, fallback journey roots, `.journey-cache`, Mermaid/Graphviz/Markdown renderers) |
| **CDS** | `.ddls`, `.cds`, `.ddlx` (`define table`, `define type`, views) |
| **DDIC** | abapGit `.tabl.xml`, ADT `.ddl`, `.dd02l`/`.dd03l` exports, domain/data element ADT XML |
| **HANA** | calculation / analytic / attribute views (`.calculationview`, `.hdbview`, `.hdbtable`) |
| **BW** | ADSO (`.adso`), DTP (`.dtp`), InfoObject (`.infoobject`), composite providers |
| **Datasphere** | analytical model JSON, `.dsview`, `.dataflow` exports |
| **OData in SAP context** | `$metadata.xml`, `.edmx`, embedded OData JSON; CLI **`--odata-url`** |
| **BAPI / IDoc / transport** | `.bapi.json`, `.idoc`, transport header/data files |
| **External Lineage** | dbt `manifest.json`, Snowflake DDL, Kafka `.avsc`, Informatica XML (`parser.include_external: true`) |

For **standalone OData CSDL** catalogs (not SAP repo export), use [OData skill](../mdengine-ai-odata/SKILL.md) (`md-odata`).

## CLI Parameter Specification (`md-sap`)

| Parameter | Type | Default | Description / Choices |
|-----------|------|---------|-----------------------|
| `input_paths` | `str...` | Positional | Files or directories containing SAP artifacts |
| `-o`, `--output` | `Path` | `./sap-out` | Destination output directory for generated Markdown |
| `--config` | `Path` | `None` | Path to YAML configuration file |
| `--pipeline-version` | `int` | `1` | `1` = legacy IR + NetworkX graph; `2` = canonical graph + `navigation/index.json` + typed generators |
| `--include` | `str` | All | Comma-separated features: `entities`, `technical`, `functional`, `relationships`, `lineage`, `governance`, `authorization`, `validations`, `graphs`, `chunks`, `json_output`, `odata_catalog` |
| `--exclude` | `str` | `None` | Comma-separated feature flags to disable |
| `--include-cds` | `flag` | `False` | Enable CDS view & type parsing |
| `--include-ddic` | `flag` | `False` | Enable Eclipse ADT & abapGit DDIC parsing |
| `--include-lineage` | `flag` | `False` | Enable data lineage extraction |
| `--include-governance` | `flag` | `False` | Enable rule validation & governance checks |
| `--graph` | `flag` | `False` | Generate NetworkX / Mermaid artifact relationship graphs |
| `--chunk` | `flag` | `False` | Produce semantic JSONL chunks for RAG pipelines |
| `--json-output` | `flag` | `False` | Export canonical JSON representation alongside Markdown |
| `--odata-url` | `str` | `None` | Repeatable live `$metadata` URL to pull OData catalogs |
| `--abap-journey` | `flag` | `False` | Enable ABAP execution journey & call graph generation |
| `--journey-depth` | `int` | `5` | Maximum call graph traversal depth for ABAP journeys |
| `--journey-format` | `str` | `md,mermaid` | Comma-separated journey formats: `md`, `mermaid`, `dot`, `json` |
| `-w`, `--workers` | `int` | `4` | Number of parallel worker threads for pipeline v2 |
| `--async` | `flag` | `False` | Run job asynchronously via SQLite job manager |

## YAML Configuration Schema (`sap-export.yaml`)

```yaml
input:
  paths: ["./sap-exports", "./wbobj/dictionary"]
  odata_urls: ["https://host/sap/opu/odata/sap/API_PRODUCT/$metadata"]
output:
  path: ./sap-out
  split_files: true
  markdown_cross_links: true
pipeline:
  version: 2                           # 1 or 2
  semantic_narrative: true             # Generate relationship narrative text
  canonical_json: true                 # Output json/canonical/
  artifact_graph: true                 # Export graph/artifacts.json
  rule_engine: true                    # Run deterministic governance rules
parser:
  include_hana: true
  include_bw: true
  include_datasphere: true
  include_external: false              # dbt, Snowflake DDL, Kafka
abap_journey:
  traversal:
    max_depth: 5
    fallback_roots: true
  renderers:
    markdown: true
    mermaid: true
    graphviz: false
  cache:
    enabled: true
    cache_dir: ./.journey-cache
features:
  include: [entities, lineage, governance, odata_catalog, graphs, chunks]
performance:
  workers: 4
```

## Examples

Concrete commands and YAML snippets: [references/example.md](references/example.md).

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
- **Notable areas:** `cli`, `api`, `core` (extractor, jobs, features), `parser` (abap, cds, ddic, hana, bw, datasphere, odata, …), `abap_journey` (resolver, graph_builder, engine, renderers), `markdown`, `orchestration`, `lineage`, `graph`

## HTTP API & MCP Parameter Specification

Env prefix **`SAP_TO_MD_`**: `SAP_TO_MD_HOST` (default `127.0.0.1`), `SAP_TO_MD_PORT` (default **8020**), `SAP_TO_MD_MAX_SYNC_ZIP_MB` (default `64`), `SAP_TO_MD_JOB_SQLITE_PATH`, `SAP_TO_MD_JOB_WORKSPACE_ROOT`, `SAP_TO_MD_CORS_ORIGINS`.

Routes (`md_generator.sap.api.main:app`):

- `GET /health`
- `POST /sap-to-md/run` — JSON body matching `SapRunConfig` schema → returns synchronous ZIP bundle
- `POST /sap-to-md/job` — JSON body matching `SapRunConfig` schema → returns `{ "job_id": "<id>", "status": "PENDING" }`
- `GET /sap-to-md/job/{job_id}` — returns job status JSON (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`)
- `GET /sap-to-md/job/{job_id}/download` — returns ZIP artifact when status is `COMPLETED`
- MCP endpoint at **`/mcp`** (Streamable HTTP MCP)

Full tables: [http-api-mcp.md](../mdengine-reference/references/http-api-mcp.md).

## See also

- [OData skill](../mdengine-ai-odata/SKILL.md) — dedicated CSDL/$metadata export
- [Global architecture skill](../global-skill.md)
- [Consumer global skill](../mdengine-ai-global/SKILL.md)
- [CLI reference](../mdengine-reference/SKILL.md)

