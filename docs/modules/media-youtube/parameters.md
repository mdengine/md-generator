# YouTube Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `url` | str | required | — | — | YouTube watch / youtu.be / shorts URL |
| `output` | Path | required | — | — | Output .md file path |
| `--title` | str | optional | None | — | Override title in Markdown |
| `--transcript-lang` | str | optional | None | — | Preferred transcript language (repeatable), e.g. --transcript-lang hi --transcript-lang en |
| `--transcript-langs` | str | optional | None | — | Comma-separated preferred transcript languages (alternative to --transcript-lang) |
| `--no-audio-fallback` | flag | optional | false | — | Do not download audio with yt-dlp + Whisper if captions are missing |
| `--whisper-model` | str | optional | 'base' | — | Whisper model when audio fallback runs (default: base) |
| `--language` | str | optional | None | — | Whisper language when audio fallback runs (same semantics as md-audio) |
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
| YOUTUBE_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

_No entries detected._


## Options / dataclass fields (sample)

_No entries detected._


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `youtube`.
