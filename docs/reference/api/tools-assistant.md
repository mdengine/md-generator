# `md_generator.tools.assistant` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Skill bundles and prompts to Assembled context and assistant output |
| CLI | `mdengine ai assist` |
| Extra | `skill-openai or skill-rag-chroma` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `query` | str | required | — | — | Natural language query |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |
| `--format` | str | optional | — | ('openai', 'claude', 'cursor') | — |
| `--query` | str | optional | — | — | Natural language query |
| `--output` | str | optional | None | — | Write to file instead of stdout. |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |
| `query` | str | required | — | — | Natural language query |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |
| `--format` | str | optional | — | ('openai', 'claude', 'cursor') | — |
| `--query` | str | optional | — | — | Natural language query |
| `--output` | str | optional | None | — | Write to file instead of stdout. |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| Registry | callable | — |
| MasterAgent | callable | — |
| run_assist | callable | — |
| run_export | callable | — |


## Python API (mkdocstrings)

::: md_generator.tools.assistant
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
