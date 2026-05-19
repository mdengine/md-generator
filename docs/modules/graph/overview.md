# Graph Metadata Module Overview

## Purpose

The **Graph Metadata** module (`md_generator.graph`) converts **Neo4j or NetworkX GraphML/GML** into **Node/relationship Markdown, Mermaid, Graphviz**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Neo4j or NetworkX GraphML/GML into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Neo4j or NetworkX GraphML/GML.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `graph` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.graph` |
| Source tree | `src/md_generator/graph` |
| CLI | `md-graph` |
- Alternate entry: `mdengine graph-to-md`
| PyPI extra | `graph` |
| Complexity tier | `medium` |
| API service name | `graph-to-md` |

## Primary entry points

- `extract_to_markdown`
- `Neo4jAdapter`
- `GraphRunConfig`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[graph_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


