# `md_generator.ppt` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert PPTX slide decks to Slide Markdown and extracted assets |
| CLI | `md-ppt` |
| Extra | `ppt` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
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


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_pptx | callable | — |
| ConvertOptions | callable | — |
| build_artifact_zip_bytes | callable | — |


## Python API (mkdocstrings)

::: md_generator.ppt
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
