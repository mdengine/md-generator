# PowerPoint Module Overview

## Purpose

The **PowerPoint** module (`md_generator.ppt`) converts **PPTX slide decks** into **Slide Markdown and extracted assets**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from PPTX slide decks into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from PPTX slide decks.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `ppt` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.ppt` |
| Source tree | `src/md_generator/ppt` |
| CLI | `md-ppt` |
| PyPI extra | `ppt` |
| Complexity tier | `medium` |
| API service name | `ppt-to-md` |

## Primary entry points

- `convert_pptx`
- `ConvertOptions`
- `build_artifact_zip_bytes`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[ppt_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


