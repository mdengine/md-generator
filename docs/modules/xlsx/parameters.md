# Excel and CSV Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `-i` | Path | optional | — | — | Path to .xlsx, .xlsm, or .csv file |
| `-o` | Path | optional | — | — | Output directory |
| `--config` | Path | optional | None | — | JSON ConvertConfig file |
| `--split` | flag | optional | false | — | One .md file per worksheet |
| `--include-hidden-sheets` | flag | optional | false | — | Include hidden worksheets |
| `--no-toc` | flag | optional | false | — | Omit table of contents (combined mode) |
| `--streaming` | flag | optional | false | — | Read-only OpenPyXL mode (no merged expansion) |
| `--no-expand-merged` | flag | optional | false | — | Do not fill merged cell ranges |
| `--max-rows` | int | optional | None | — | Max rows per sheet |
| `--sheet` | str | optional | None | — | Export only sheet(s) with this name (repeatable, case-insensitive) |
| `--log-level` | str | optional | 'INFO' | ('DEBUG', 'INFO', 'WARNING', 'ERROR') | — |


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
| XLSX_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertConfig | include_hidden_sheets | bool | varies | — | Field on options/config class |
| ConvertConfig | max_rows_per_sheet | int | varies | — | Field on options/config class |
| ConvertConfig | sheet_names | list[str] \| None | varies | — | Field on options/config class |
| ConvertConfig | split_by_sheet | bool | varies | — | Field on options/config class |
| ConvertConfig | sheet_heading_level | HeadingLevel | varies | — | Field on options/config class |
| ConvertConfig | include_toc | bool | varies | — | Field on options/config class |
| ConvertConfig | column_indices | list[int] \| None | varies | — | Field on options/config class |
| ConvertConfig | column_names | list[str] \| None | varies | — | Field on options/config class |
| ConvertConfig | column_alignment | list[Alignment] | varies | — | Field on options/config class |
| ConvertConfig | enable_alignment_in_tables | bool | varies | — | Field on options/config class |
| ConvertConfig | expand_merged_cells | bool | varies | — | Field on options/config class |
| ConvertConfig | streaming | bool | varies | — | Field on options/config class |
| ConvertConfig | output_basename | str \| None | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `xlsx`.
