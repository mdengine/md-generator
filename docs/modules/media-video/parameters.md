# Video Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input video file path |
| `output` | Path | required | — | — | Output .md file path |
| `--model` | str | optional | 'base' | — | Whisper model name (default: base) |
| `--language` | str | optional | None | — | Whisper language (default: auto-detect if omitted). Single code/name (e.g. en, hi) to force, or hi,en / hinglish for Hindi+English mixed. Explicit auto / detect matches omitting the flag. |
| `--title` | str | optional | None | — | Override document title in Markdown |
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
| VIDEO_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

_No entries detected._


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `video`.
