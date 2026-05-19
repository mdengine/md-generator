# Log Analysis Module Overview

## Purpose

The **Log Analysis** module (`md_generator.log`) converts **Log files and uploads** into **Parsed events, summaries, incidents, optional clustering**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Log files and uploads into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Log files and uploads.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `log` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.log` |
| Source tree | `src/md_generator/log` |
| CLI | `md-log` |
- Alternate entry: `mdengine log-to-md`
| PyPI extra | `log` |
| Complexity tier | `complex` |
| API service name | `log-to-md` |

## Primary entry points

- `extract_to_markdown`
- `run_pipeline`
- `LogRunConfig`
- `load_run_config`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[log_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


