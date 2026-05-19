# Image OCR Module Overview

## Purpose

The **Image OCR** module (`md_generator.image`) converts **Image files or directories** into **OCR Markdown and metadata**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Image files or directories into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Image files or directories.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `image or image-ocr` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.image` |
| Source tree | `src/md_generator/image` |
| CLI | `md-image` |
| PyPI extra | `image or image-ocr` |
| Complexity tier | `medium` |
| API service name | `image-to-md` |

## Primary entry points

- `convert_images`
- `convert_images_recursive`
- `build_backends`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[image_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


