# Skill Builder Module Overview

## Purpose

The **Skill Builder** module (`md_generator.tools.skill_builder`) converts **Project metadata** into **Structured skills under ai/**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Project metadata into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Project metadata.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `(base package)` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.tools.skill_builder` |
| Source tree | `src/md_generator/tools/skill_builder` |
| CLI | `mdengine skill build` |
| PyPI extra | `(base package)` |
| Complexity tier | `medium` |
| API service name | `(none)` |

## Primary entry points

- `run_generate`
- `build_dependency_graph`
- `build_routing_block`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[tools-skill-builder_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


