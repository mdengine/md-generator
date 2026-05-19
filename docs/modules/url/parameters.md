# URL and Web Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `url` | str | required | — | — | Single HTTP or HTTPS URL |
| `output` | Path | required | — | — | Output .md file or directory (with --artifact-layout); omit when using --urls-file with -o |
| `-o` | Path | optional | None | — | Output directory for --urls-file (bulk) mode |
| `--urls-file` | Path | optional | None | — | Text file with one URL per line |
| `--artifact-layout` | flag | optional | false | — | Write document.md + assets/ under output dir |
| `--crawl` | flag | optional | false | — | Breadth-first crawl (requires --artifact-layout) |
| `--async-crawl` | flag | optional | false | — | Use async HTTP + parallel page fetches (requires --crawl); default is sync crawl |
| `--crawl-max-concurrency` | int | optional | 4 | — | Max concurrent page fetches when --async-crawl (default: 4, max: 32) |
| `--max-depth` | int | optional | 2 | — | — |
| `--max-pages` | int | optional | 30 | — | — |
| `--crawl-delay` | float | optional | 0.5 | — | Seconds between crawl requests |
| `--no-robots` | flag | optional | false | — | Do not consult robots.txt |
| `--no-subdomains` | flag | optional | false | — | Only exact same host when following links |
| `--images-dir` | Path | optional | None | — | Classic mode: image directory (default: <md parent>/images) |
| `--timeout` | float | optional | 30.0 | — | — |
| `--max-response-mb` | float | optional | 10.0 | — | — |
| `--no-table-csv` | flag | optional | false | — | — |
| `--no-linked-files` | flag | optional | false | — | Skip downloading linked PDF/ZIP/etc. |
| `--max-linked-files` | int | optional | 40 | — | Max linked file downloads per page (default: 40) |
| `--max-downloaded-images` | int | optional | 50 | — | Max image downloads per page (default: 50) |
| `--no-convert-downloaded-assets` | flag | optional | false | — | Do not run internal converters on files under assets/files/ |
| `--no-convert-downloaded-images` | flag | optional | false | — | Skip OCR for raster images under assets/images/ (default: run when mdengine[image] is installed) |
| `--convert-downloaded-image-to-md-engines` | str | optional | DEFAULT_IMAGE_TO_MD_ENGINES | — | Comma-separated OCR engines for downloaded images: tess, paddle, easy (default: %(default)s) |
| `--convert-downloaded-image-to-md-strategy` | str | optional | 'best' | ('best', 'compare') | How to combine engine outputs for downloaded images (default: "best") |
| `--convert-downloaded-image-to-md-title` | str | optional | '' | — | Markdown title inside the bundled OCR file (default: empty → "Downloaded images (OCR)") |
| `--post-convert-pdf-ocr` | flag | optional | false | — | When converting downloaded PDFs, enable page OCR like md-pdf --ocr |
| `--no-post-convert-ppt-embedded` | flag | optional | false | — | When converting downloaded PPTX, disable deep embedded extraction |
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
| URL_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ConvertOptions | artifact_layout | bool | varies | — | Field on options/config class |
| ConvertOptions | images_dir | Path \| None | varies | — | Field on options/config class |
| ConvertOptions | verbose | bool | varies | — | Field on options/config class |
| ConvertOptions | timeout_seconds | float | varies | — | Field on options/config class |
| ConvertOptions | max_response_bytes | int | varies | — | Field on options/config class |
| ConvertOptions | user_agent | str | varies | — | Field on options/config class |
| ConvertOptions | table_csv | bool | varies | — | Field on options/config class |
| ConvertOptions | download_linked_files | bool | varies | — | Field on options/config class |
| ConvertOptions | linked_file_extensions | tuple[str, ...] | varies | — | Field on options/config class |
| ConvertOptions | max_linked_files | int | varies | — | Field on options/config class |
| ConvertOptions | max_downloaded_images | int | varies | — | Field on options/config class |
| ConvertOptions | crawl | bool | varies | — | Field on options/config class |
| ConvertOptions | max_depth | int | varies | — | Field on options/config class |
| ConvertOptions | max_pages | int | varies | — | Field on options/config class |
| ConvertOptions | crawl_delay_seconds | float | varies | — | Field on options/config class |
| ConvertOptions | async_crawl | bool | varies | — | Field on options/config class |
| ConvertOptions | crawl_max_concurrency | int | varies | — | Field on options/config class |
| ConvertOptions | obey_robots | bool | varies | — | Field on options/config class |
| ConvertOptions | same_site_only | bool | varies | — | Field on options/config class |
| ConvertOptions | include_subdomains | bool | varies | — | Field on options/config class |
| ConvertOptions | convert_downloaded_assets | bool | varies | — | Field on options/config class |
| ConvertOptions | convert_downloaded_images | bool | varies | — | Field on options/config class |
| ConvertOptions | convert_downloaded_image_to_md_engines | str | varies | — | Field on options/config class |
| ConvertOptions | convert_downloaded_image_to_md_strategy | str | varies | — | Field on options/config class |
| ConvertOptions | convert_downloaded_image_to_md_title | str | varies | — | Field on options/config class |
| ConvertOptions | post_convert_pdf_ocr | bool | varies | — | Field on options/config class |
| ConvertOptions | post_convert_pdf_ocr_min_chars | int | varies | — | Field on options/config class |
| ConvertOptions | post_convert_ppt_embedded_deep | bool | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `url or url-full`.
