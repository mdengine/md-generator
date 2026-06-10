# `md_generator.odata` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert OData CSDL metadata (XML/JSON), folders, ZIP archives, or $metadata URLs to Entity catalog Markdown, optional graph and semantic chunks |
| CLI | `md-odata` |
| Extra | `odata` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `--file` | Path | optional | None | — | Path to metadata.xml/json |
| `--folder` | Path | optional | None | — | Directory containing OData metadata |
| `--zip` | Path | optional | None | — | ZIP archive containing metadata |
| `--url` | str | optional | [] | — | Fetch $metadata from URL (repeatable) |
| `--config` | Path | optional | None | — | YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--graph` | flag | optional | false | — | Export relationship graph |
| `--chunk` | flag | optional | false | — | Write semantic chunks |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| extract_to_markdown | callable | — |
| OdataRunConfig | callable | — |
| load_odata_run_config | callable | — |
| build_markdown_zip_bytes | callable | — |


## Python API (mkdocstrings)

::: md_generator.odata
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
