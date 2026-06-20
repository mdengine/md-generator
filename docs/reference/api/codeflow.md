# `md_generator.codeflow` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Source repositories to Architecture Markdown, graphs, flow docs, JSON, Mermaid |
| CLI | `md-codeflow` |
| Extra | `codeflow` |
| Tier | `complex` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `path` | str | required | None | — | Local directory, source file, .zip, or https/git remote URL (omit when using --clean-git-cache only) |
| `--output` | Path | optional | None | — | Output directory |
| `--entry` | str | optional | None | — | Comma-separated symbol ids (Class.method style) |
| `--lang` | str | optional | 'mixed' | — | mixed \| python \| java \| javascript \| typescript \| tsx \| cpp \| go \| php \| rust \| kotlin \| csharp \| swift \| ruby \| lua \| scala \| zig \| comma-separated (e.g. python,javascript). Aliases: js→javascript, ts→typescript. |
| `--formats` | str | optional | None | — | Comma-separated: md,html,mermaid,json |
| `--depth` | int | optional | 5 | — | — |
| `--include` | str | optional | None | — | Filter entry kinds: api,event,main,... |
| `--exclude` | str | optional | None | — | Reserved for path/symbol exclusions |
| `--async` | flag | optional | True | — | — |
| `--no-async` | str | optional | — | — | — |
| `--jobs` | flag | optional | False | — | No-op in CLI (reserved for API) |
| `--runtime` | flag | optional | False | — | Reserved: runtime tracing |
| `--business-rules` | str | optional | True | — | Emit business_rules.md, entry section, and (unless disabled) entry.combined.md (default: on) |
| `--business-rules-sql` | flag | optional | False | — | Scan workspace *.sql for CREATE TRIGGER lines |
| `--business-rules-combined` | str | optional | True | — | Write entry.combined.md (entry.md + business_rules.md) (default: on) |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| run_scan | callable | — |
| ScanConfig | callable | — |
| build_output_zip | callable | — |
| build_graph | callable | — |


## Python API (mkdocstrings)

::: md_generator.codeflow
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
