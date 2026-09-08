---
name: mdengine-openapi-agent
description: >-
  Assists with pip-installed mdengine OpenAPI → Markdown / docs bundle: choosing extras and using public
  CLIs/APIs under md_generator.openapi. Use when tasks involve md-openapi, openapi, swagger, md_generator.openapi and do not
  require editing mdengine source in a git checkout.
version: 0.7.0
---

# mdengine agent — OpenAPI → Markdown / docs bundle

## Mission

Guide operators and integrators to the **published** commands and APIs for **OpenAPI → Markdown / docs bundle** after `pip install mdengine[...]`.

## Boundaries

- **In scope:** installed behavior, flags, extras, ports, MCP tools as documented upstream.
- **Out of scope:** internal file paths inside the mdengine git repository (e.g. `src/...`); those concern upstream maintainers only.

## Orchestration

- **Multi-area queries:** use [Master agent](../agent/master-agent.md) (registry routing + `dependency-graph.json` + response schema).

## Handoff

- **Global agent:** [mdengine-global-agent.md](mdengine-global-agent.md) for cross-area installs and version pinning.
- **Humans:** production secrets, compliance, resource limits (GPU, Whisper model size).

## Primary skill

See [Primary skill](../skills/mdengine-ai-openapi/SKILL.md).

## Parameter & Execution Guidance

- **CLI Operations:** Run `md-openapi generate -f openapi.yaml -o ./openapi-out --graph --chunk`. Handles automatic in-process conversion of Swagger 2.0 to OpenAPI 3.0.3.
- **REST API:** Target `POST /openapi-to-md/generate` on port `OPENAPI_TO_MD_PORT` (default 8015).
- **MCP:** Target `md-openapi-mcp` or streamable HTTP at `/mcp` (`api_validate_openapi_yaml`, `api_generate_readme_markdown`, `api_run_sync_zip_base64`).

