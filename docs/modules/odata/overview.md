# OData Metadata Module Overview

## Purpose

The **OData Metadata** module (`md_generator.odata`) converts **OData CSDL metadata (XML/JSON), folders, ZIP archives, or $metadata URLs** into **Entity catalog Markdown, optional graph and semantic chunks**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from OData CSDL metadata (XML/JSON), folders, ZIP archives, or $metadata URLs into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from OData CSDL metadata (XML/JSON), folders, ZIP archives, or $metadata URLs.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `odata` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.odata` |
| Source tree | `src/md_generator/odata` |
| CLI | `md-odata` |
| Alternate CLI | `mdengine odata-to-md generate` |
| PyPI extra | `odata` |
| Complexity tier | `medium` |
| API service name | `odata-to-md` |

## Primary entry points

- `extract_to_markdown`
- `OdataRunConfig`
- `load_odata_run_config`
- `build_markdown_zip_bytes`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[odata_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


