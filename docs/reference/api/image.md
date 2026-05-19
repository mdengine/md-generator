# `md_generator.image` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Image files or directories to OCR Markdown and metadata |
| CLI | `md-image` |
| Extra | `image or image-ocr` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
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


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_images | callable | — |
| convert_images_recursive | callable | — |
| build_backends | callable | — |


## Python API (mkdocstrings)

::: md_generator.image
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
