# AI Assistant Tools Module Overview

## Purpose

The **AI Assistant Tools** module (`md_generator.tools.assistant`) converts **Skill bundles and prompts** into **Assembled context and assistant output**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Skill bundles and prompts into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Skill bundles and prompts.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `skill-openai or skill-rag-chroma` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.tools.assistant` |
| Source tree | `src/md_generator/tools/assistant` |
| CLI | `mdengine ai assist` |
| Alternate CLI | `mdengine ai export` |
| PyPI extra | `skill-openai or skill-rag-chroma` |
| Complexity tier | `medium` |
| API service name | `(none)` |

## Primary entry points

- `Registry`
- `MasterAgent`
- `run_assist`
- `run_export`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[tools-assistant_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


