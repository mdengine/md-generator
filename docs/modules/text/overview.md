# Text JSON XML Module Overview

## Purpose

The **Text JSON XML** module (`md_generator.text`) converts **TXT, JSON, XML** into **Readable Markdown representations**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from TXT, JSON, XML into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from TXT, JSON, XML.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `text` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.text` |
| Source tree | `src/md_generator/text` |
| CLI | `md-text` |
| PyPI extra | `text` |
| Complexity tier | `simple` |
| API service name | `txt-json-xml-to-md` |

## Primary entry points

- `convert_text_file`
- `json_to_markdown`
- `xml_to_markdown`
- `detect_format`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[text_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


