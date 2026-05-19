# `md_generator.text` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert TXT, JSON, XML to Readable Markdown representations |
| CLI | `md-text` |
| Extra | `text` |
| Tier | `simple` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input .txt, .json, or .xml path |
| `output` | Path | required | — | — | Output .md file or directory (with --artifact-layout) |
| `--artifact-layout` | flag | optional | false | — | Write document.md under output directory |
| `--encoding` | str | optional | 'utf-8' | — | Text encoding for input (default: utf-8) |
| `--format` | str | optional | 'auto' | ('auto', 'txt', 'json', 'xml') | Input format (default: auto from extension or sniff) |
| `--no-source-block` | flag | optional | false | — | Do not append original JSON/XML in a fenced code block |
| `--toc` | flag | optional | false | — | Insert a table of contents for JSON/XML section headings |
| `--structure` | str | optional | 'hierarchical' | ('hierarchical', 'flattened') | JSON/XML: nested headings (default) or flattened paths grouped as headings |
| `--xml-parser` | str | optional | 'auto' | ('auto', 'stdlib', 'lxml') | XML hierarchical mode only: parse with stdlib, lxml, or auto (prefer lxml if installed) |
| `-v` | flag | optional | false | — | — |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| convert_text_file | callable | — |
| json_to_markdown | callable | — |
| xml_to_markdown | callable | — |
| detect_format | callable | — |


## Python API (mkdocstrings)

::: md_generator.text
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
