# Video CLI Reference

Command: **`md-video`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input video file path |
| `output` | Path | required | — | — | Output .md file path |
| `--model` | str | optional | 'base' | — | Whisper model name (default: base) |
| `--language` | str | optional | None | — | Whisper language (default: auto-detect if omitted). Single code/name (e.g. en, hi) to force, or hi,en / hinglish for Hindi+English mixed. Explicit auto / detect matches omitting the flag. |
| `--title` | str | optional | None | — | Override document title in Markdown |
| `-v` | flag | optional | false | — | — |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
