# PDF CLI Reference

Command: **`md-pdf`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input_pdf` | Path | required | — | — | Input .pdf path |
| `output` | Path | required | — | — | Output .md path or directory with --artifact-layout |
| `--artifact-layout` | flag | optional | false | — | Write OUTPUT/document.md and OUTPUT/assets/images/ |
| `--images-dir` | Path | optional | None | — | Image directory (classic mode only; default: <parent of output.md>/images) |
| `--ocr` | flag | optional | false | — | OCR pages with little embedded text |
| `--ocr-min-chars` | int | optional | 40 | — | Embedded text below this length triggers OCR when --ocr (default: 40) |
| `-v` | flag | optional | false | — | Print warnings to stderr |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
