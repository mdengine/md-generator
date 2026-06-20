# Word Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input_docx` | Path | required | — | — | Input .docx path |
| `output_md` | Path | required | — | — | Output .md path |
| `--images-dir` | Path | optional | None | — | Directory for extracted images (default: <parent of output>/images) |
| `--no-page-break-hr` | flag | optional | false | — | Do not map page-break-like spans to horizontal rules |
| `-v` | flag | optional | false | — | — |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| POST | /convert/sync | HTTP | — | — | FastAPI route |
| POST | /convert/jobs | HTTP | — | — | FastAPI route |
| GET | /convert/jobs/{job_id} | HTTP | — | — | FastAPI route |
| GET | /convert/jobs/{job_id}/download | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| WORD_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| WordToMdSettings | max_upload_mb | float | varies | — | Field on options/config class |
| WordToMdSettings | max_sync_upload_mb | float | varies | — | Field on options/config class |
| WordToMdSettings | job_ttl_seconds | int | varies | — | Field on options/config class |
| WordToMdSettings | temp_dir | str | varies | — | Field on options/config class |
| WordToMdSettings | cors_origins | tuple[str, ...] | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `word`.
