# Excel and CSV CLI Reference

Command: **`md-xlsx`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `-i` | Path | optional | — | — | Path to .xlsx, .xlsm, or .csv file |
| `-o` | Path | optional | — | — | Output directory |
| `--config` | Path | optional | None | — | JSON ConvertConfig file |
| `--split` | flag | optional | false | — | One .md file per worksheet |
| `--include-hidden-sheets` | flag | optional | false | — | Include hidden worksheets |
| `--no-toc` | flag | optional | false | — | Omit table of contents (combined mode) |
| `--streaming` | flag | optional | false | — | Read-only OpenPyXL mode (no merged expansion) |
| `--no-expand-merged` | flag | optional | false | — | Do not fill merged cell ranges |
| `--max-rows` | int | optional | None | — | Max rows per sheet |
| `--sheet` | str | optional | None | — | Export only sheet(s) with this name (repeatable, case-insensitive) |
| `--log-level` | str | optional | 'INFO' | ('DEBUG', 'INFO', 'WARNING', 'ERROR') | — |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
