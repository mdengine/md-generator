# `md_generator.tools.skill_builder` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Project metadata to Structured skills under ai/ |
| CLI | `mdengine skill build` |
| Extra | `(base package)` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--since` | str | optional | None | — | Only regenerate area skills touched under src/md_generator since GIT_REF (global/graph/registry still refresh). |
| `--root` | Path | optional | _REPO_ROOT | — | Repository root (default: inferred from this file). |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| run_generate | callable | — |
| build_dependency_graph | callable | — |
| build_routing_block | callable | — |


## Python API (mkdocstrings)

::: md_generator.tools.skill_builder
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
