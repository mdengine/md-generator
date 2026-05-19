# PowerPoint CLI Reference

Command: **`md-ppt`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input .pptx path |
| `output` | Path | required | — | — | Output .md file or directory (with --artifact-layout) |
| `--artifact-layout` | flag | optional | false | — | Write document.md + assets/ under output dir |
| `--images-dir` | Path | optional | None | — | Image directory (classic mode only) |
| `--no-title-slide-h1` | flag | optional | false | — | Use ## for all slide titles (classic) |
| `--no-strip-known-footers` | flag | optional | false | — | — |
| `-v` | flag | optional | false | — | — |
| `--max-unpack-depth` | int | optional | 2 | — | — |
| `--no-chart-data` | flag | optional | false | — | — |
| `--no-chart-image` | flag | optional | false | — | — |
| `--no-table-csv` | flag | optional | false | — | — |
| `--extract-embedded-deep` | flag | optional | false | — | — |
| `--no-extract-embedded-deep` | str | optional | — | — | — |
| `--no-extracted-txt-md` | flag | optional | false | — | — |
| `--no-extracted-docx-md` | flag | optional | false | — | — |
| `--no-extracted-pdf-md` | flag | optional | false | — | — |
| `--no-extracted-xlsx-md` | flag | optional | false | — | — |
| `--extracted-pdf-ocr` | flag | optional | false | — | — |
| `--no-extracted-pdf-ocr` | str | optional | — | — | — |
| `--extracted-pdf-ocr-min-chars` | int | optional | 50 | — | — |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
