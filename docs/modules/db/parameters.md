# Database Metadata Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
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
| `--test-connection` | flag | optional | false | — | Validate database connectivity and exit (no export) |
| `--list-schemas` | flag | optional | false | — | Print schema names (or catalog labels) and exit |
| `--output-format` | str | optional | 'text' | ('text', 'json') | Output format for --list-schemas |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run/sqlite | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job/sqlite | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run/access | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job/access | HTTP | — | — | FastAPI route |
| POST | /db-to-md/run | HTTP | — | — | FastAPI route |
| POST | /db-to-md/job | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id} | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id}/download | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id}/events | HTTP | — | — | FastAPI route |
| GET | /db-to-md/job/{job_id}/stream | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| DB_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\db\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## Options / dataclass fields (sample)

_No entries detected._


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `db`.
