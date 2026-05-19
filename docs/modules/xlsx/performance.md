# Excel and CSV Performance

## Characteristics

| Area | Notes |
|------|-------|
| CPU | Hotspots in parsing, OCR, Whisper, browser capture, graph/DB introspection |
| Memory | Full-file reads for some converters; prefer job API for large inputs |
| Disk | Artifact layouts multiply image/asset size |
| Parallelism | Domain modules may use worker pools (`--workers` on db/log) |

## Recommendations

- Use async job endpoints for large ZIP outputs.
- Pin worker counts to available CPU.
- For batch fleets, horizontal-scale stateless API pods with shared object storage for job artifacts if extended beyond local disk.
