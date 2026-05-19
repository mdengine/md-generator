# `md_generator.log` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Log files and uploads to Parsed events, summaries, incidents, optional clustering |
| CLI | `md-log` |
| Extra | `log` |
| Tier | `complex` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | YAML config path |
| `--input` | Path | optional | None | — | Log file or directory (repeatable) |
| `--output` | Path | optional | None | — | Output directory |
| `--preset` | str | optional | None | — | Parser preset name (e.g. generic, springboot, logback, json) |
| `--line-regex` | str | optional | None | — | Custom line regex (named groups: timestamp, level, message, …) |
| `--auto-detect` | flag | optional | false | — | Auto-detect parser preset from log sample |
| `--preset-dir` | str | optional | None | — | Directory with user preset YAML files (repeatable; also MD_LOG_PRESET_DIRS, ~/.mdengine/log/presets) |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; SQLite job store) |
| `--export-jsonl` | flag | optional | false | — | Export embedding-ready JSONL chunks |
| `--export-parquet` | flag | optional | false | — | Export embedding-ready Parquet chunks |
| `--resume` | flag | optional | false | — | Enable incremental checkpoint resume |
| `--frontmatter` | flag | optional | false | — | Emit YAML frontmatter on artifacts |
| `--source` | str | optional | 'tail' | ['tail', 'stdin', 'kafka', 'redis', 'websocket'] | — |
| `--config` | Path | optional | None | — | — |
| `--input` | Path | optional | None | — | File path for tail source |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| extract_to_markdown | callable | — |
| run_pipeline | callable | — |
| LogRunConfig | callable | — |
| load_run_config | callable | — |


## Python API (mkdocstrings)

::: md_generator.log
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
