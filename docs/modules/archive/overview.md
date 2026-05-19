# ZIP Archive Module Overview

## Purpose

The **ZIP Archive** module (`md_generator.archive`) converts **ZIP archives** into **Directory-oriented Markdown bundle**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from ZIP archives into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from ZIP archives.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `archive plus nested format extras` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.archive` |
| Source tree | `src/md_generator/archive` |
| CLI | `md-zip` |
| PyPI extra | `archive plus nested format extras` |
| Complexity tier | `medium` |
| API service name | `zip-to-md` |

## Primary entry points

- `convert_archive`
- `convert_zip`
- `extract_archive`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[archive_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


