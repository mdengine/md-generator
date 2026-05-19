# Excel and CSV Module Overview

## Purpose

The **Excel and CSV** module (`md_generator.xlsx`) converts **XLSX, XLSM, CSV** into **Worksheet or CSV Markdown tables**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from XLSX, XLSM, CSV into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from XLSX, XLSM, CSV.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `xlsx` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.xlsx` |
| Source tree | `src/md_generator/xlsx` |
| CLI | `md-xlsx` |
| PyPI extra | `xlsx` |
| Complexity tier | `simple` |
| API service name | `xlsx-to-md` |

## Primary entry points

- `convert_excel_to_markdown`
- `ConvertConfig`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[xlsx_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


