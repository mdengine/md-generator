# Word Module Overview

## Purpose

The **Word** module (`md_generator.word`) converts **DOCX documents** into **Markdown with optional embedded images**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from DOCX documents into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from DOCX documents.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `word` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.word` |
| Source tree | `src/md_generator/word` |
| CLI | `md-word` |
| PyPI extra | `word` |
| Complexity tier | `simple` |
| API service name | `word-to-md` |

## Primary entry points

- `convert_docx_to_markdown`
- `WordToMdSettings`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[word_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


