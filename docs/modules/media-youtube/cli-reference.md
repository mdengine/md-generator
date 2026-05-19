# YouTube CLI Reference

Command: **`md-youtube`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
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


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
