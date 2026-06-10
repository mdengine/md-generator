# SAP Intelligence CLI Reference

Command: **`md-sap`**  
Alternate: `mdengine sap-to-md`

## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `input` | Path | required | — | — | SAP source paths (files or directories) |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--output` | Path | optional | None | — | Output directory |
| `--include` | str | optional | None | — | Comma-separated feature list |
| `--exclude` | str | optional | None | — | — |
| `--include-cds` | flag | optional | false | — | Enable CDS parser |
| `--include-ddic` | flag | optional | false | — | Enable DDIC parser |
| `--include-lineage` | flag | optional | false | — | Enable lineage analyzer |
| `--include-governance` | flag | optional | false | — | Enable governance analyzer |
| `--graph` | flag | optional | false | — | Export relationship graphs |
| `--chunk` | flag | optional | false | — | Write semantic chunks |
| `--json-output` | flag | optional | false | — | Include json_output feature |
| `--odata-url` | str | optional | [] | — | Fetch OData $metadata from URL (repeatable) |
| `--async` | flag | optional | false | — | Run as background job |
| `--pipeline-version` | int | optional | None | — | Pipeline version (1=legacy, 2=canonical+graph) |
| `--workers` | int | optional | None | — | Parallel parser workers |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
