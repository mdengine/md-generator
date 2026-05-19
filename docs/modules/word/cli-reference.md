# Word CLI Reference

Command: **`md-word`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input_docx` | Path | required | — | — | Input .docx path |
| `output_md` | Path | required | — | — | Output .md path |
| `--images-dir` | Path | optional | None | — | Directory for extracted images (default: <parent of output>/images) |
| `--no-page-break-hr` | flag | optional | false | — | Do not map page-break-like spans to horizontal rules |
| `-v` | flag | optional | false | — | — |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
