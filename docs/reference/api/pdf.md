# `md_generator.pdf` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert PDF documents to Markdown with optional artifact layout and extracted images |
| CLI | `md-pdf` |
| Extra | `pdf` |
| Tier | `simple` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `input_pdf` | Path | required | — | — | Input .pdf path |
| `output` | Path | required | — | — | Output .md path or directory with --artifact-layout |
| `--artifact-layout` | flag | optional | false | — | Write OUTPUT/document.md and OUTPUT/assets/images/ |
| `--images-dir` | Path | optional | None | — | Image directory (classic mode only; default: <parent of output.md>/images) |
| `--ocr` | flag | optional | false | — | OCR pages with little embedded text |
| `--ocr-min-chars` | int | optional | 40 | — | Embedded text below this length triggers OCR when --ocr (default: 40) |
| `-v` | flag | optional | false | — | Print warnings to stderr |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_pdf | callable | — |
| convert_pdf_to_artifact_dir | callable | — |
| ConvertOptions | callable | — |


## Python API (mkdocstrings)

::: md_generator.pdf
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
