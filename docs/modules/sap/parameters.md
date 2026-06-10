# SAP Intelligence Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | SAP source paths (files or directories) |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--include-cds` | flag | optional | false | — | Enable CDS parser |
| `--include-ddic` | flag | optional | false | — | Enable DDIC parser |
| `--include-lineage` | flag | optional | false | — | Enable lineage analyzer |
| `--include-governance` | flag | optional | false | — | Enable governance analyzer |
| `--graph` | flag | optional | false | — | Export relationship graphs |
| `--chunk` | flag | optional | false | — | Write semantic chunks |
| `--json-output` | flag | optional | false | — | Include json_output feature |
| `--odata-url` | str | optional | [] | — | Fetch OData $metadata from URL (repeatable) |
| `--async` | flag | optional | false | — | Run as background job |
| `--pipeline-version` | int | optional | None | — | Pipeline version (1=legacy, 2=canonical+graph) |
| `--workers` | int | optional | None | — | Parallel parser workers |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /sap-to-md/run | HTTP | — | — | FastAPI route |
| POST | /sap-to-md/job | HTTP | — | — | FastAPI route |
| GET | /sap-to-md/job/{job_id} | HTTP | — | — | FastAPI route |
| GET | /sap-to-md/job/{job_id}/download | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| SAP_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\sap\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## Options / dataclass fields (sample)

_No entries detected._


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `sap`.
