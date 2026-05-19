# PowerPoint Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input .pptx path |
| `output` | Path | required | — | — | Output .md file or directory (with --artifact-layout) |
| `--artifact-layout` | flag | optional | false | — | Write document.md + assets/ under output dir |
| `--images-dir` | Path | optional | None | — | Image directory (classic mode only) |
| `--no-title-slide-h1` | flag | optional | false | — | Use ## for all slide titles (classic) |
| `--no-strip-known-footers` | flag | optional | false | — | — |
| `-v` | flag | optional | false | — | — |
| `--max-unpack-depth` | int | optional | 2 | — | — |
| `--no-chart-data` | flag | optional | false | — | — |
| `--no-chart-image` | flag | optional | false | — | — |
| `--no-table-csv` | flag | optional | false | — | — |
| `--extract-embedded-deep` | flag | optional | false | — | — |
| `--no-extract-embedded-deep` | str | optional | — | — | — |
| `--no-extracted-txt-md` | flag | optional | false | — | — |
| `--no-extracted-docx-md` | flag | optional | false | — | — |
| `--no-extracted-pdf-md` | flag | optional | false | — | — |
| `--no-extracted-xlsx-md` | flag | optional | false | — | — |
| `--extracted-pdf-ocr` | flag | optional | false | — | — |
| `--no-extracted-pdf-ocr` | str | optional | — | — | — |
| `--extracted-pdf-ocr-min-chars` | int | optional | 50 | — | — |


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
| PPT_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertOptions | artifact_layout | bool | varies | — | Field on options/config class |
| ConvertOptions | images_dir | Path \| None | varies | — | Field on options/config class |
| ConvertOptions | title_slide_h1 | bool | varies | — | Field on options/config class |
| ConvertOptions | strip_known_footers | bool | varies | — | Field on options/config class |
| ConvertOptions | verbose | bool | varies | — | Field on options/config class |
| ConvertOptions | max_unpack_depth | int | varies | — | Field on options/config class |
| ConvertOptions | chart_data | bool | varies | — | Field on options/config class |
| ConvertOptions | chart_image | bool | varies | — | Field on options/config class |
| ConvertOptions | table_csv | bool | varies | — | Field on options/config class |
| ConvertOptions | extract_embedded_deep | bool | varies | — | Field on options/config class |
| ConvertOptions | emit_extracted_txt_md | bool | varies | — | Field on options/config class |
| ConvertOptions | extracted_docx_md | bool | varies | — | Field on options/config class |
| ConvertOptions | extracted_pdf_md | bool | varies | — | Field on options/config class |
| ConvertOptions | extracted_xlsx_md | bool | varies | — | Field on options/config class |
| ConvertOptions | extracted_pdf_ocr | bool | varies | — | Field on options/config class |
| ConvertOptions | extracted_pdf_ocr_min_chars | int | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `ppt`.
