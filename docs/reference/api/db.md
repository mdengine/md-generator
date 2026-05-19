# `md_generator.db` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Postgres, MySQL, Oracle, SQLite, Mongo, Access to Schema docs, ERD, Markdown ZIP |
| CLI | `md-db` |
| Extra | `db` |
| Tier | `complex` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--type` | str | optional | None | — | postgres\|mysql\|mssql\|oracle\|mongo\|sqlite\|access |
| `--uri` | str | optional | None | — | — |
| `--output` | Path | optional | None | — | — |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--schema` | str | optional | None | — | — |
| `--database` | str | optional | None | — | Mongo database name |
| `--split-files` | str | optional | None | ('true', 'false') | — |
| `--workers` | int | optional | None | — | — |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; uses SQLite job store) |
| `--erd-max-tables` | int | optional | None | — | ERD: max tables (default from config, usually 100) |
| `--erd-scope` | str | optional | None | ('full', 'per_schema', 'per_table') | ERD: full \| per_schema \| per_table |
| `--write-combined-feature-markdown` | str | optional | None | ('true', 'false') | When split_files, also write root tables.md, views.md, … bundles |
| `--readme-feature-merge` | str | optional | None | ('none', 'inline', 'toc') | Append combined bundle docs to README: none \| inline \| toc |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| extract_to_markdown | callable | — |
| create_adapter | callable | — |
| RunConfig | callable | — |
| JobManager | callable | — |


## Python API (mkdocstrings)

::: md_generator.db
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
