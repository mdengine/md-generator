# `md_generator.word` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert DOCX documents to Markdown with optional embedded images |
| CLI | `md-word` |
| Extra | `word` |
| Tier | `simple` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `input_docx` | Path | required | — | — | Input .docx path |
| `output_md` | Path | required | — | — | Output .md path |
| `--images-dir` | Path | optional | None | — | Directory for extracted images (default: <parent of output>/images) |
| `--no-page-break-hr` | flag | optional | false | — | Do not map page-break-like spans to horizontal rules |
| `-v` | flag | optional | false | — | — |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_docx_to_markdown | callable | — |
| WordToMdSettings | callable | — |


## Python API (mkdocstrings)

::: md_generator.word
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
