# OpenTelemetry Traces CLI Reference

Command: **`md-otel`**  
Alternate: `mdengine otel-to-md`

## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--input` | Path | optional | — | — | — |
| `--output` | Path | optional | Path('./otel-docs') | — | — |
| `--protobuf` | flag | optional | false | — | — |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
