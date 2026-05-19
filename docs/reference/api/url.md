# `md_generator.url` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert HTTP(S) pages to Cleaned Markdown and optional artifacts |
| CLI | `md-url` |
| Extra | `url or url-full` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
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


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_url | callable | — |
| run_crawl | callable | — |
| convert_one_page_artifact | callable | — |


## Python API (mkdocstrings)

::: md_generator.url
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
