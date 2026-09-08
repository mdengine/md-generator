---
name: mdengine-odata-agent
description: >-
  Assists with pip-installed mdengine OData → Markdown: choosing the `odata` extra
  and using md-odata, md-odata-api, md-odata-mcp under md_generator.odata. Use when
  tasks involve CSDL/$metadata export, odata-to-md, or OData service documentation
  and do not require editing mdengine source in a git checkout.
version: 0.13.0
---

# mdengine agent — OData → Markdown

## Mission

Guide operators and integrators to the **published** commands and APIs for **odata-to-md** after `pip install mdengine[...]`.

## Boundaries

- **In scope:** installed behavior, `generate` subcommand flags, extras, `ODATA_TO_MD_*` settings, API routes, MCP transports and tool names.
- **Out of scope:** internal repository paths under `src/...` for upstream maintainers only.
- **Not OpenAPI:** OData CSDL metadata is distinct from OpenAPI/Swagger specs — hand off to [mdengine-openapi-agent.md](mdengine-openapi-agent.md) when the input is an OpenAPI document.

## Orchestration

- **Multi-area queries:** use [Master agent](../agent/master-agent.md) (registry routing + `dependency-graph.json` + response schema).

## Handoff

- **Global agent:** [mdengine-global-agent.md](mdengine-global-agent.md) for cross-area installs and version pinning.
- **OpenAPI:** [mdengine-openapi-agent.md](mdengine-openapi-agent.md) for Swagger/OpenAPI YAML/JSON bundles.
- **SAP OData parsers:** [mdengine-sap-agent.md](mdengine-sap-agent.md) when SAP-specific OData/XML artifacts are in scope.

## Primary skill

See [Primary skill](../skills/mdengine-ai-odata/SKILL.md).

## Parameter & Execution Guidance

- **CLI Operations:** Run `md-odata generate -f metadata.xml -o ./odata-out` or `md-odata generate -u "https://host/service/$metadata" -o ./odata-out --graph --chunk`.
- **REST API:** Target `POST /odata-to-md/generate` on port `ODATA_TO_MD_PORT` (default 8017).
- **MCP:** Target `md-odata-mcp` or streamable HTTP at `/mcp` (`odata_validate_metadata`, `odata_generate_readme_markdown`, `odata_run_sync_zip_base64`).

