# Log Analysis Exceptions

## CLI exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Conversion failure |
| 2 | Usage / missing input |

## HTTP errors

| Status | Typical cause |
|--------|----------------|
| 400 | Invalid input/empty upload |
| 413 | Payload exceeds configured MB limit |
| 404 | Unknown job id |
| 500 | Unhandled conversion error |

Wrap calls with retry only for transient network fetch modules (url, youtube); converter failures usually require input fixes.
