# ZIP Archive Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input archive path |
| `output` | Path | required | — | — | Output directory (writes document.md and assets/) |
| `-v` | flag | optional | false | — | — |
| `--no-office` | flag | optional | false | — | Skip PDF/DOCX/PPTX/XLSX conversion |
| `--image-ocr` | flag | optional | false | — | Run tesseract on extracted images |
| `--no-image-ocr` | str | optional | — | — | — |
| `--use-image-to-md` | flag | optional | false | — | Enable post-pass image-to-md OCR (default: on); see --image-to-md-engines |
| `--no-use-image-to-md` | str | optional | — | — | Disable post-pass image-to-md over assets/files and assets/images |
| `--image-to-md-engines` | str | optional | DEFAULT_IMAGE_TO_MD_ENGINES | — | — |
| `--image-to-md-strategy` | str | optional | 'best' | ('best', 'compare') | image-to-md --strategy (default: best) |
| `--image-to-md-title` | str | optional | '' | — | Top-level title passed to image-to-md (default: derived from filename) |
| `--pdf-ocr` | flag | optional | false | — | Pass --ocr to pdf-to-md for nested PDFs |
| `--max-bytes` | int | optional | 512000 | — | Max UTF-8 bytes for inlined text bodies (default: 512000) |
| `--repo-root` | Path | optional | None | — | Deprecated: ignored (install extras, e.g. mdengine[pdf,word], for embedded office files) |
| `--no-expand-nested-zips` | flag | optional | false | — | Do not recursively extract nested archives under assets/files/ |
| `--max-nested-zip-depth` | int | optional | 16 | — | Max nesting depth for inner archives (each *_unzipped/ segment counts as one level; default: 16) |


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
| ZIP_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertOptions | verbose | bool | varies | — | Field on options/config class |
| ConvertOptions | artifact_layout | bool | varies | — | Field on options/config class |
| ConvertOptions | enable_office | bool | varies | — | Field on options/config class |
| ConvertOptions | image_ocr | bool | varies | — | Field on options/config class |
| ConvertOptions | pdf_ocr | bool | varies | — | Field on options/config class |
| ConvertOptions | max_bytes | int | varies | — | Field on options/config class |
| ConvertOptions | repo_root | str \| None | varies | — | Field on options/config class |
| ConvertOptions | expand_nested_zips | bool | varies | — | Field on options/config class |
| ConvertOptions | max_nested_zip_depth | int | varies | — | Field on options/config class |
| ConvertOptions | use_image_to_md | bool | varies | — | Field on options/config class |
| ConvertOptions | image_to_md_engines | str | varies | — | Field on options/config class |
| ConvertOptions | image_to_md_strategy | str | varies | — | Field on options/config class |
| ConvertOptions | image_to_md_title | str | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `archive plus nested format extras`.
