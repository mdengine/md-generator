# Database Metadata CLI Reference

Command: **`md-db`**  
Alternate: `mdengine db-to-md`

## Arguments

| Name | Type | Required | Default | Choices | Description |
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
| `--write-combined-feature-markdown` | str | optional | None | ('true', 'false') | When split_files, also write root tables.md, views.md, … bundles |
| `--readme-feature-merge` | str | optional | None | ('none', 'inline', 'toc') | Append combined bundle docs to README: none \| inline \| toc |
| `--test-connection` | flag | optional | false | — | Validate database connectivity and exit (no export) |
| `--list-schemas` | flag | optional | false | — | Print schema names (or catalog labels) and exit |
| `--output-format` | str | optional | 'text' | ('text', 'json') | Output format for --list-schemas |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
