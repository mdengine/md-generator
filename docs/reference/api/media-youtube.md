# `md_generator.media.youtube` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert YouTube URLs to Transcript and metadata Markdown |
| CLI | `md-youtube` |
| Extra | `youtube` |
| Tier | `simple` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `url` | str | required | — | — | YouTube watch / youtu.be / shorts URL |
| `output` | Path | required | — | — | Output .md file path |
| `--title` | str | optional | None | — | Override title in Markdown |
| `--transcript-lang` | str | optional | None | — | Preferred transcript language (repeatable), e.g. --transcript-lang hi --transcript-lang en |
| `--transcript-langs` | str | optional | None | — | Comma-separated preferred transcript languages (alternative to --transcript-lang) |
| `--no-audio-fallback` | flag | optional | false | — | Do not download audio with yt-dlp + Whisper if captions are missing |
| `--whisper-model` | str | optional | 'base' | — | Whisper model when audio fallback runs (default: base) |
| `--language` | str | optional | None | — | Whisper language when audio fallback runs (same semantics as md-audio) |
| `-v` | flag | optional | false | — | — |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| YouTubeToMarkdownService | callable | — |
| YouTubeConverter | callable | — |


## Python API (mkdocstrings)

::: md_generator.media.youtube
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
