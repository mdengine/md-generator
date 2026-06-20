# Image OCR Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input image file or directory of images |
| `output` | Path | required | — | — | Output .md path, or output directory with --artifact-layout |
| `--artifact-layout` | flag | optional | false | — | Treat OUTPUT as a directory and write document.md inside it |
| `--engines` | str | optional | 'tess,paddle,easy' | — | Comma-separated engines: tess, paddle, easy (default: tess,paddle,easy) |
| `--strategy` | str | optional | 'compare' | ('compare', 'best') | compare: section per engine; best: longest non-empty text (tie: earlier engine wins) |
| `--title` | str | optional | 'OCR extraction' | — | Top-level Markdown heading |
| `--lang` | str | optional | 'eng' | — | Tesseract language (default: eng) |
| `--paddle-lang` | str | optional | 'en' | — | PaddleOCR lang code (default: en) |
| `--paddle-no-angle-cls` | flag | optional | false | — | Disable PaddleOCR angle classifier |
| `--easy-lang` | str | optional | 'en' | — | Comma-separated EasyOCR language codes (default: en) |
| `--tesseract-cmd` | str | optional | None | — | Path to tesseract executable (default: env TESSERACT_CMD or TESSERACT_PATH) |
| `-v` | flag | optional | false | — | Print dependency/runtime warnings to stderr |


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
| IMAGE_TO_MD_TEMP_DIR | string/int | optional | — | — | From `src\md_generator\image\api\settings.py` |
| IMAGE_TO_MD_CORS_ORIGINS | string/int | optional | — | — | From `src\md_generator\image\api\settings.py` |
| IMAGE_TO_MD_TESSERACT_CMD | string/int | optional | — | — | From `src\md_generator\image\api\settings.py` |
| TESSERACT_CMD | string/int | optional | — | — | From `src\md_generator\image\api\settings.py` |
| IMAGE_TO_MD_MAX_UPLOAD_MB | string/int | optional | — | — | Derived env pattern in `settings.py` |
| IMAGE_TO_MD_MAX_SYNC_UPLOAD_MB | string/int | optional | — | — | Derived env pattern in `settings.py` |
| IMAGE_TO_MD_JOB_TTL_SECONDS | string/int | optional | — | — | Derived env pattern in `settings.py` |
| IMAGE_TO_MD_PORT | string/int | optional | — | — | Derived env pattern in `settings.py` |


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertOptions | engines | tuple[str, ...] | varies | — | Field on options/config class |
| ConvertOptions | strategy | Literal['compare', 'best'] | varies | — | Field on options/config class |
| ConvertOptions | title | str | varies | — | Field on options/config class |
| ConvertOptions | tess_lang | str | varies | — | Field on options/config class |
| ConvertOptions | tesseract_cmd | str \| None | varies | — | Field on options/config class |
| ConvertOptions | paddle_lang | str | varies | — | Field on options/config class |
| ConvertOptions | paddle_use_angle_cls | bool | varies | — | Field on options/config class |
| ConvertOptions | easy_langs | tuple[str, ...] | varies | — | Field on options/config class |
| ConvertOptions | verbose | bool | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `image or image-ocr`.
