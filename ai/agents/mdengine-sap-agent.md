---
name: mdengine-sap-agent
description: >-
  Assists with pip-installed mdengine SAP → Markdown: choosing the `sap` extra
  and using md-sap, md-sap-api, md-sap-mcp under md_generator.sap. Use when tasks
  involve ABAP/CDS/DDIC, HANA/BW/Datasphere artifacts, sap-to-md, `--odata-url`,
  or SAP documentation and do not require editing mdengine source in a git checkout.
version: 0.13.0
---

# mdengine agent — SAP → Markdown

## Mission

Guide operators and integrators to the **published** commands and APIs for **sap-to-md** after `pip install mdengine[...]`.

## Boundaries

- **In scope:** installed behavior, flags, extras, `SAP_TO_MD_*` settings, API routes, MCP transports.
- **Out of scope:** internal repository paths under `src/...` for upstream maintainers only.

## Orchestration

- **Multi-area queries:** use [Master agent](../agent/master-agent.md) (registry routing + `dependency-graph.json` + response schema).

## Handoff

- **Global agent:** [mdengine-global-agent.md](mdengine-global-agent.md) for cross-area installs and version pinning.
- **OData CSDL-only:** [mdengine-odata-agent.md](mdengine-odata-agent.md) when input is `$metadata` without broader SAP repo context.

## Primary skill

See [Primary skill](../skills/mdengine-ai-sap/SKILL.md).
