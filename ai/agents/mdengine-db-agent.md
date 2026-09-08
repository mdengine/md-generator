---
name: mdengine-db-agent
description: >-
  Assists with pip-installed mdengine Database → Markdown: choosing extras and using public
  CLIs/APIs under md_generator.db. Use when tasks involve md-db, database to markdown, ERD, SQL metadata, md_generator.db and do not
  require editing mdengine source in a git checkout.
version: 0.7.0
---

# mdengine agent — Database → Markdown

## Mission

Guide operators and integrators to the **published** commands and APIs for **Database → Markdown** after `pip install mdengine[...]`.

## Boundaries

- **In scope:** installed behavior, flags, extras, ports, MCP tools as documented upstream.
- **Out of scope:** internal file paths inside the mdengine git repository (e.g. `src/...`); those concern upstream maintainers only.

## Orchestration

- **Multi-area queries:** use [Master agent](../agent/master-agent.md) (registry routing + `dependency-graph.json` + response schema).

## Handoff

- **Global agent:** [mdengine-global-agent.md](mdengine-global-agent.md) for cross-area installs and version pinning.
- **Humans:** production secrets, compliance, resource limits (GPU, Whisper model size).

## Primary skill

See [Primary skill](../skills/mdengine-ai-db/SKILL.md).

## Parameter & Execution Guidance

- **CLI Operations:** Run `md-db --config <db-export.yaml>` or `md-db --type <engine> --schema <schema>`. Use `--write-combined-feature-markdown` and `--readme-feature-merge inline` for split outputs. Tune ERD thresholds via `--erd-max-tables` and `--erd-scope`.
- **REST API:** Target `POST /db-to-md/run` (or `/run/sqlite`, `/run/access`, `/run/elasticsearch` for single-file uploads) on port `DB_TO_MD_PORT` (default 8010).
- **MCP:** Target `md-db-mcp` (`db_export_metadata`, `db_export_sqlite_base64`) or streamable HTTP at `/mcp`.

