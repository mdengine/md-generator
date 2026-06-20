# OpenAPI Module Overview

## Purpose

The **OpenAPI** module (`md_generator.openapi`) converts **OpenAPI 3.x or Swagger 2.0** into **API documentation ZIP bundle**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from OpenAPI 3.x or Swagger 2.0 into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from OpenAPI 3.x or Swagger 2.0.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `openapi` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.openapi` |
| Source tree | `src/md_generator/openapi` |
| CLI | `md-openapi` |
| Alternate CLI | `mdengine openapi-to-md generate` |
| PyPI extra | `openapi` |
| Complexity tier | `medium` |
| API service name | `openapi-to-md` |

## Primary entry points

- `extract_to_markdown`
- `load_spec`
- `swagger2_to_openapi3`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[openapi_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


