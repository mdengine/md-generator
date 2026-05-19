# ZIP Archive CLI Reference

Command: **`md-zip`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | Input archive path |
| `output` | Path | required | — | — | Output directory (writes document.md and assets/) |
| `-v` | flag | optional | false | — | — |
| `--no-office` | flag | optional | false | — | Skip PDF/DOCX/PPTX/XLSX conversion |
| `--image-ocr` | flag | optional | false | — | Run tesseract on extracted images |
| `--no-image-ocr` | str | optional | — | — | — |
| `--use-image-to-md` | flag | optional | false | — | Enable post-pass image-to-md OCR (default: on); see --image-to-md-engines |
| `--no-use-image-to-md` | str | optional | — | — | Disable post-pass image-to-md over assets/files and assets/images |
| `--image-to-md-engines` | str | optional | DEFAULT_IMAGE_TO_MD_ENGINES | — | — |
| `--image-to-md-strategy` | str | optional | 'best' | ('best', 'compare') | image-to-md --strategy (default: best) |
| `--image-to-md-title` | str | optional | '' | — | Top-level title passed to image-to-md (default: derived from filename) |
| `--pdf-ocr` | flag | optional | false | — | Pass --ocr to pdf-to-md for nested PDFs |
| `--max-bytes` | int | optional | 512000 | — | Max UTF-8 bytes for inlined text bodies (default: 512000) |
| `--repo-root` | Path | optional | None | — | Deprecated: ignored (install extras, e.g. mdengine[pdf,word], for embedded office files) |
| `--no-expand-nested-zips` | flag | optional | false | — | Do not recursively extract nested archives under assets/files/ |
| `--max-nested-zip-depth` | int | optional | 16 | — | Max nesting depth for inner archives (each *_unzipped/ segment counts as one level; default: 16) |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
