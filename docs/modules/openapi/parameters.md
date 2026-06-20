# OpenAPI Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

_No entries detected._


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /openapi-to-md/generate | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| OPENAPI_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\openapi\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## YAML config keys (from packaged defaults)

| File | Key | Default / sample | Required | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\openapi\config\default.yaml | input.file | null | optional | — | From packaged YAML |
| src\md_generator\openapi\config\default.yaml | input.folder | null | optional | — | From packaged YAML |
| src\md_generator\openapi\config\default.yaml | input.zip | null | optional | — | From packaged YAML |
| src\md_generator\openapi\config\default.yaml | input.url | null | optional | — | From packaged YAML |
| src\md_generator\openapi\config\default.yaml | output.path | './docs' | optional | — | From packaged YAML |
| src\md_generator\openapi\config\default.yaml | output.formats | 'md', 'mermaid' | optional | — | From packaged YAML |
| src\md_generator\openapi\config\default.yaml | openapi.preferred_media_type | 'application/json' | optional | — | From packaged YAML |


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

_No entries detected._


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `openapi`.
