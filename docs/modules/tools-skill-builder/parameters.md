# Skill Builder Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--since` | str | optional | None | — | Only regenerate area skills touched under src/md_generator since GIT_REF (global/graph/registry still refresh). |
| `--root` | Path | optional | _REPO_ROOT | — | Repository root (default: inferred from this file). |


## API routes (HTTP parameters)

_No entries detected._


## Environment variables

_No entries detected._


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
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `(base package)`.
