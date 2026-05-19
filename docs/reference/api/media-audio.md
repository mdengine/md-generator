# `md_generator.media.audio` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Audio files to Whisper transcript Markdown |
| CLI | `md-audio` |
| Extra | `audio` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input audio file path |
| `output` | Path | required | — | — | Output .md file path |
| `--model` | str | optional | 'base' | — | Whisper model name (default: base) |
| `--language` | str | optional | None | — | Whisper language (default: auto-detect if omitted). Single code/name (e.g. en, hi) to force, or hi,en / hinglish for Hindi+English mixed (auto-detect + bilingual prompt). Explicit auto / detect is the same as omitting this flag. |
| `--title` | str | optional | None | — | Override document title in Markdown |
| `-v` | flag | optional | false | — | — |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| DocumentConverter | callable | — |
| AudioConverter | callable | — |


## Python API (mkdocstrings)

::: md_generator.media.audio
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
