# Video Module Overview

## Purpose

The **Video** module (`md_generator.media.video`) converts **Video files** into **Transcript Markdown with video metadata**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Video files into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Video files.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `video` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.media.video` |
| Source tree | `src/md_generator/media/video` |
| CLI | `md-video` |
| PyPI extra | `video` |
| Complexity tier | `medium` |
| API service name | `video-to-md` |

## Primary entry points

- `VideoToMarkdownService`
- `video_probe_from_ffprobe`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[media-video_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


