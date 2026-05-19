# `md_generator.media.video` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert Video files to Transcript Markdown with video metadata |
| CLI | `md-video` |
| Extra | `video` |
| Tier | `medium` |

## Quick CLI reference

| Argument | Type | Required | Default | Choices | Help |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input video file path |
| `output` | Path | required | — | — | Output .md file path |
| `--model` | str | optional | 'base' | — | Whisper model name (default: base) |
| `--language` | str | optional | None | — | Whisper language (default: auto-detect if omitted). Single code/name (e.g. en, hi) to force, or hi,en / hinglish for Hindi+English mixed. Explicit auto / detect matches omitting the flag. |
| `--title` | str | optional | None | — | Override document title in Markdown |
| `-v` | flag | optional | false | — | — |


## Primary symbols

| Symbol | Kind | Notes |
| --- | --- | --- |
| VideoToMarkdownService | callable | — |
| video_probe_from_ffprobe | callable | — |


## Python API (mkdocstrings)

::: md_generator.media.video
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
