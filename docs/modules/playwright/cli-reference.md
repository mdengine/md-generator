# Playwright Web Capture CLI Reference

Command: **`md-playwright`**  


## Arguments

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


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
