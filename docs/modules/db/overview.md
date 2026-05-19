# Database Metadata Module Overview

## Purpose

The **Database Metadata** module (`md_generator.db`) converts **Postgres, MySQL, Oracle, SQLite, Mongo, Access** into **Schema docs, ERD, Markdown ZIP**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from Postgres, MySQL, Oracle, SQLite, Mongo, Access into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from Postgres, MySQL, Oracle, SQLite, Mongo, Access.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `db` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `md_generator.db` |
| Source tree | `src/md_generator/db` |
| CLI | `md-db` |
- Alternate entry: `mdengine db-to-md`
| PyPI extra | `db` |
| Complexity tier | `complex` |
| API service name | `db-to-md` |

## Primary entry points

- `extract_to_markdown`
- `create_adapter`
- `RunConfig`
- `JobManager`

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[db_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```


