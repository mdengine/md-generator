# `md_generator.db` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Postgres, MySQL, Oracle, SQLite, Mongo, Access, Elasticsearch/OpenSearch clusters and offline JSON bundles to Schema docs, ERD, Markdown ZIP; Elasticsearch indices, templates, pipelines, ILM/SLM, search templates, alias and dependency graphs |
| CLI | `md-db` |
| Extra | `db` |
| Tier | `complex` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--type` | str | optional | None | — | postgres\|mysql\|mssql\|oracle\|mongo\|sqlite\|access\|elasticsearch |
| `--uri` | str | optional | None | — | — |
| `--output` | Path | optional | None | — | — |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--schema` | str | optional | None | — | — |
| `--database` | str | optional | None | — | Mongo database name |
| `--index-pattern` | str | optional | None | — | Elasticsearch index pattern (stored in limits.index_pattern) |
| `--list-indices` | flag | optional | false | — | List index names for Elasticsearch and exit (alias for --list-schemas) |
| `--split-files` | str | optional | None | ('true', 'false') | — |
| `--workers` | int | optional | None | — | — |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; uses SQLite job store) |
| `--erd-max-tables` | int | optional | None | — | ERD: max tables (default from config, usually 100) |
| `--erd-scope` | str | optional | None | ('full', 'per_schema', 'per_table') | ERD: full \| per_schema \| per_table |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| extract_to_markdown | callable | — |
| create_adapter | callable | — |
| RunConfig | callable | — |
| JobManager | callable | — |
| export_elasticsearch_markdown | callable | — |


## Python API (mkdocstrings)

::: md_generator.db
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
