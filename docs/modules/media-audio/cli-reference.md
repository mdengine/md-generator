# Audio CLI Reference

Command: **`md-audio`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input audio file path |
| `output` | Path | required | — | — | Output .md file path |
| `--model` | str | optional | 'base' | — | Whisper model name (default: base) |
| `--language` | str | optional | None | — | Whisper language (default: auto-detect if omitted). Single code/name (e.g. en, hi) to force, or hi,en / hinglish for Hindi+English mixed (auto-detect + bilingual prompt). Explicit auto / detect is the same as omitting this flag. |
| `--title` | str | optional | None | — | Override document title in Markdown |
| `-v` | flag | optional | false | — | — |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
