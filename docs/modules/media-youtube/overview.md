# YouTube Module Overview

## Purpose

The **YouTube** module (`md_generator.media.youtube`) converts **YouTube URLs** into **Transcript and metadata Markdown**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from YouTube URLs into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from YouTube URLs.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `youtube` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.media.youtube` |
| Source tree | `src/md_generator/media/youtube` |
| CLI | `md-youtube` |
| PyPI extra | `youtube` |
| Complexity tier | `simple` |
| API service name | `youtube-to-md` |

## Primary entry points

- `YouTubeToMarkdownService`
- `YouTubeConverter`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[media-youtube_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


