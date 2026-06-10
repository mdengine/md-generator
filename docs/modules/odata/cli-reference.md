# OData Metadata CLI Reference

Command: **`md-odata`**  
Alternate: `mdengine odata-to-md generate`

## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--file` | Path | optional | None | — | Path to metadata.xml/json |
| `--folder` | Path | optional | None | — | Directory containing OData metadata |
| `--zip` | Path | optional | None | — | ZIP archive containing metadata |
| `--url` | str | optional | [] | — | Fetch $metadata from URL (repeatable) |
| `--config` | Path | optional | None | — | YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--graph` | flag | optional | false | — | Export relationship graph |
| `--chunk` | flag | optional | false | — | Write semantic chunks |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
