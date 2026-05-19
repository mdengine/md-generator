# Playwright Web Capture Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `url` | str | required | — | — | HTTP or HTTPS URL to fetch |
| `--output` | Path | optional | Path('.') | — | Output directory (default: current directory) |
| `--wait` | str | optional | None | — | Optional CSS selector to wait for before scrolling |
| `--timeout` | float | optional | 60.0 | — | Navigation timeout in seconds (default: 60) |
| `--user-agent` | str | optional | None | — | Override browser User-Agent |
| `--wait-until` | str | optional | 'networkidle' | ('load', 'domcontentloaded', 'commit', 'networkidle') | Playwright goto wait_until (default: networkidle) |
| `--max-scroll-rounds` | int | optional | 12 | — | Max scroll-to-bottom iterations for lazy loading (default: 12) |
| `--retries` | int | optional | 3 | — | Max fetch attempts with backoff (default: 3) |
| `--no-chunk` | flag | optional | false | — | Disable chunk markers in output Markdown |
| `--no-readability` | flag | optional | false | — | Skip readability pass before markdownify |
| `--screenshot` | Path | optional | None | — | Save full-page PNG screenshot to this path |
| `--save-raw-html` | Path | optional | None | — | Save raw rendered HTML to this path |
| `--max-chunk-tokens` | int | optional | 900 | — | Approximate max tokens per chunk (default: 900) |
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
| PLAYWRIGHT_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config file parameters

_No entries detected._


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| PlaywrightOptions | verbose | bool | varies | — | Field on options/config class |
| PlaywrightOptions | navigation_timeout_ms | float | varies | — | Field on options/config class |
| PlaywrightOptions | user_agent | str | varies | — | Field on options/config class |
| PlaywrightOptions | wait_selector | str \| None | varies | — | Field on options/config class |
| PlaywrightOptions | wait_until | WaitUntil | varies | — | Field on options/config class |
| PlaywrightOptions | max_scroll_rounds | int | varies | — | Field on options/config class |
| PlaywrightOptions | scroll_pause_ms | float | varies | — | Field on options/config class |
| PlaywrightOptions | max_retries | int | varies | — | Field on options/config class |
| PlaywrightOptions | retry_backoff_seconds | float | varies | — | Field on options/config class |
| PlaywrightOptions | headless | bool | varies | — | Field on options/config class |
| PlaywrightOptions | use_readability | bool | varies | — | Field on options/config class |
| PlaywrightOptions | chunk_markdown | bool | varies | — | Field on options/config class |
| PlaywrightOptions | max_chunk_tokens | int | varies | — | Field on options/config class |
| PlaywrightOptions | chars_per_token | int | varies | — | Field on options/config class |
| PlaywrightOptions | max_images | int | varies | — | Field on options/config class |
| PlaywrightOptions | max_image_bytes | int | varies | — | Field on options/config class |
| PlaywrightOptions | asset_timeout_seconds | float | varies | — | Field on options/config class |
| PlaywrightOptions | screenshot_path | Path \| None | varies | — | Field on options/config class |
| PlaywrightOptions | save_raw_html_path | Path \| None | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `playwright`.
