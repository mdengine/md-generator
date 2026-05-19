# PDF Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input_pdf` | Path | required | — | — | Input .pdf path |
| `output` | Path | required | — | — | Output .md path or directory with --artifact-layout |
| `--artifact-layout` | flag | optional | false | — | Write OUTPUT/document.md and OUTPUT/assets/images/ |
| `--images-dir` | Path | optional | None | — | Image directory (classic mode only; default: <parent of output.md>/images) |
| `--ocr` | flag | optional | false | — | OCR pages with little embedded text |
| `--ocr-min-chars` | int | optional | 40 | — | Embedded text below this length triggers OCR when --ocr (default: 40) |
| `-v` | flag | optional | false | — | Print warnings to stderr |


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
| PDF_TO_MD_TEMP_DIR | string/int | optional | — | — | From `src\md_generator\pdf\api\settings.py` |
| PDF_TO_MD_CORS_ORIGINS | string/int | optional | — | — | From `src\md_generator\pdf\api\settings.py` |
| PDF_TO_MD_MAX_UPLOAD_MB | string/int | optional | — | — | Derived env pattern in `settings.py` |
| PDF_TO_MD_MAX_SYNC_UPLOAD_MB | string/int | optional | — | — | Derived env pattern in `settings.py` |
| PDF_TO_MD_JOB_TTL_SECONDS | string/int | optional | — | — | Derived env pattern in `settings.py` |
| PDF_TO_MD_PORT | string/int | optional | — | — | Derived env pattern in `settings.py` |


## Config file parameters

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertOptions | use_ocr | bool | varies | — | Field on options/config class |
| ConvertOptions | ocr_min_chars | int | varies | — | Field on options/config class |
| ConvertOptions | verbose | bool | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `pdf`.
