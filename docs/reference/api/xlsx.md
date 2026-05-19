# `md_generator.xlsx` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert XLSX, XLSM, CSV to Worksheet or CSV Markdown tables |
| CLI | `md-xlsx` |
| Extra | `xlsx` |
| Tier | `simple` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
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


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_excel_to_markdown | callable | — |
| ConvertConfig | callable | — |


## Python API (mkdocstrings)

::: md_generator.xlsx
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
